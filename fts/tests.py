import pytest
import os
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from django.contrib.auth.models import User
import bookish.models as m
from django.core.management import call_command


@pytest.fixture(scope="module")
def browser(request):
    if 'USE_CHROME' in os.environ:
        browser = webdriver.Chrome()
    else:
        browser = webdriver.Firefox()
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


@pytest.fixture(scope="module")
def demo_users(request):
    # Create system users. Minimum is admin, accountant, and a user in a company
    User.objects.create_superuser(username='demo_admin', password='demo_admin', email='demo@example.org')
    demo_accountant = User.objects.create_user(username='demo_accountant', password='demo_accountant')
    demo_client = User.objects.create_user(username='demo_client', first_name="David", last_name="Dangerfield", password='demo_client')
    
    # Create an accountancy firm
    accountancy_firm = m.AccountancyFirm.objects.create(name="ABC Accountants")
    accountancy_firm.users.add(demo_accountant)
    
    # Create a company
    company = m.Company.objects.create(name="Demo Company", accountancy_firm=accountancy_firm, address="21 Happy Gardens, Halifax, W.Yorks, HX1 4RT", VAT_registartion_number="123456789")
    company.users.add(demo_client)


def test_admin_page_is_shown(live_server, browser):
    # Gertrude opens her web browser, and goes to the admin page
    browser.get(live_server.url + '/admin/')

    # She sees the familiar 'Django administration' heading
    body = browser.find_element_by_tag_name('body')
    assert 'Django administration' in body.text


def test_log_in(live_server, browser, demo_users):
    # Ben opens his browser and goes to the main page
    browser.get(live_server.url + '/')

    # He can see a link to log in
    body = browser.find_element_by_tag_name('body')
    assert 'Log in' in body.text

    # He can click the link...
    body.find_element_by_link_text('Log in').click()

    # .. and then submit login details
    browser.find_element_by_id('id_username').send_keys('demo_client')
    browser.find_element_by_id('id_password').send_keys('demo_client')
    browser.find_element_by_css_selector('input[type=submit]').click()
    # He can then see his user name, company name and a link to log out
    body = browser.find_element_by_tag_name('body')
    assert 'Demo Company' in body.text
    assert 'demo_client' in body.text
    assert 'Logout' in body.text


def log_in(browser, username):
    browser.find_element_by_link_text('Log in').click()
    browser.find_element_by_id('id_username').send_keys(username)
    browser.find_element_by_id('id_password').send_keys(username)
    browser.find_element_by_css_selector('input[type=submit]').click()


def test_inline_edit_cash(live_server, browser, client):
    # Set up the server with some demo data, and then login
    call_command('createdemodata')
    browser.get(live_server.url + '/')
    log_in(browser, 'demo_client')
    
    # Linda can browse to the cash page
    browser.get(live_server.url + '/cash')
    # She can't see any input boxes yet
    with pytest.raises(NoSuchElementException):
        browser.find_element_by_tag_name('input')
    # But if she clickes on the edit button
    browser.find_element_by_link_text('Edit').click()
    # she stays at the same URL (ajax!)
    assert browser.current_url == live_server.url + '/cash'
    # and can now see inputs
    browser.find_element_by_tag_name('input')
    # She can change some details on the form
    browser.find_element_by_css_selector('input[id=id_name]').clear()
    browser.find_element_by_css_selector('input[id=id_name]').send_keys('New Description')
    browser.find_element_by_css_selector('input[type=submit]').click()
    # She can no longer see the input boxes
    with pytest.raises(NoSuchElementException):
        browser.find_element_by_tag_name('input')
    # but the new details is still on the page
    assert 'New Description' in browser.find_element_by_tag_name('body').text
    # When she loads the page again, the details are still there
    browser.get(live_server.url + '/cash')
    assert 'New Description' in browser.find_element_by_tag_name('body').text
