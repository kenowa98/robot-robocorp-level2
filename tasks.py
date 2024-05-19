from robocorp       import browser
from robocorp.tasks import task

from RPA.HTTP   import HTTP
from RPA.Tables import Tables
from RPA.PDF    import PDF

import time
import zipfile
import os

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        browser_engine = "chromium",
        screenshot     = "only-on-failure",
        headless       = False,
        # slowmo         = 1000,
    )
    orders = get_orders()
    open_robot_order_website()

    for order in orders:
        fill_the_form(order)

    archive_receipts()


def get_orders():
    """Download the orders file, read it as a table, and return the result"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

    table = Tables()
    data  = table.read_table_from_csv("orders.csv")

    return data

def open_robot_order_website():
    """Navigates to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def close_annoying_modal():
    """Close pop ups"""
    page = browser.page()
    page.click("button:text('OK')")

def fill_the_form(order):
    """Fill the form with order data"""
    close_annoying_modal()

    page = browser.page()

    page.select_option("#head", str(order["Head"]))
    page.click(f"#id-body-{order['Body']}")
    page.fill("//input[@type='number' and contains(@placeholder, 'legs')]", str(order["Legs"]))
    page.fill("#address", order["Address"])
    page.click("#order")

    while True:
        error_alert = page.locator("//div[contains(@class, 'alert-danger')]")
        if error_alert.is_visible():
            time.sleep(0.5)
            page.click("#order")
        else:
            pdf        = store_receipt_as_pdf(str(order["Order number"]))
            screenshot = screenshot_robot(str(order["Order number"]))
            embed_screenshot_to_receipt(screenshot, pdf)
            break

    order_new_robot()

def store_receipt_as_pdf(order_number):
    page = browser.page()
    store_receipt_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf.html_to_pdf(store_receipt_html, f"output/receipts/robot-{order_number}.pdf")

    return f"output/receipts/robot-{order_number}.pdf"

def screenshot_robot(order_number):
    page = browser.page()
    page.screenshot(path=f"output/images/robot-{order_number}.png")

    return f"output/images/robot-{order_number}.png"

def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()

    list_of_files = [
        pdf_file,
        f'{screenshot}:align=center'
    ]
    pdf.add_files_to_pdf(
        files=list_of_files,
        target_document=pdf_file
    )

def order_new_robot():
    page = browser.page()
    page.click("#order-another")

def archive_receipts():
    directory = 'output/receipts'
    zip_name  = 'output/receipts.zip'

    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), directory))

