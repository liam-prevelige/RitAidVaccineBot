from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from pytz import timezone
import PySimpleGUI as sg


def start_driver():
    ua = UserAgent()
    user_agent = ua.random
    print(user_agent)

    opts = Options()
    opts.add_argument(f'user-agent={user_agent}')

    driver = webdriver.Chrome(r'C:\Users\preve\PycharmProjects\RiteAidBot\chromedriver.exe', options=opts)
    return driver


def check_cities_availability(state="New Jersey", cities=None):
    if cities is None:
        cities = ["Union City"]

    default_age = "11/11/1950"
    default_occupation = "Childcare Worker"
    default_medical_conditions = "None of the Above"

    try:
        driver = start_driver()
        wait = WebDriverWait(driver, 10)

        driver.maximize_window()
        driver.get("https://www.riteaid.com/covid-vaccine-apt")

        fill_in_element("dateOfBirth", default_age, driver)
        fill_in_element("city", cities[0], driver)
        fill_in_element("eligibility_state", state, driver)
        fill_in_element("Occupation", default_occupation, driver)
        fill_in_element("mediconditions", default_medical_conditions, driver)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(1)
        driver.find_element_by_xpath("//*[@id='continue']").click()

        learn_more_bttn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='learnmorebttn']")))
        time.sleep(.5)
        learn_more_bttn.click()

        for city in cities:
            wait = WebDriverWait(driver, 10)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1.5)
            # Reached searching by city
            fill_in_element("covid-store-search", city, driver, True)
            find_store_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='btn-find-store']")))
            find_store_btn.click()

            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "covid-store__store")))
            time.sleep(1)
            stores = driver.find_elements_by_class_name("covid-store__store")
            count = 1
            for store in stores:
                time.sleep(2)
                # Scroll to current store and select
                ActionChains(driver).move_to_element(store).perform()

                if count == 1:  # scroll to window containing stores if first cycle
                    driver.execute_script("window.scrollBy(0, 150);")
                    time.sleep(1)
                else:   # scroll within stores window
                    driver.execute_script("arguments[0].scrollIntoView();", store)
                    time.sleep(1)

                store_btn_x_path = "/html/body/div[1]/div/div[6]/div/div[2]/div/div/div[3]/form/div[1]/div[1]/div[2]/div[2]/div/div/div/div[3]/div[2]/div["+str(count)+"]/div[2]/div[3]/a[2]"

                wait.until(EC.element_to_be_clickable((By.XPATH, store_btn_x_path)))
                store_button = store.find_element_by_xpath(store_btn_x_path)
                store_button.click()
                time.sleep(1)

                # Scroll to and click confirm button
                confirm_store_btn = driver.find_element_by_xpath("//*[@id='continue']")

                driver.execute_script("arguments[0].scrollIntoView();", confirm_store_btn)
                time.sleep(1)
                driver.execute_script("window.scrollBy(0, -250);")
                time.sleep(1)
                wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='continue']")))
                confirm_store_btn.click()
                time.sleep(1)

                store_header_x_path = "/html/body/div[1]/div/div[6]/div/div[2]/div/div/div[3]/form/div[1]/div[1]/div[2]/div[2]/div/div/div/div[3]/div[2]/div["+str(count)+"]/div[2]/div[1]/span[1]"
                wait.until(EC.presence_of_element_located((By.XPATH, store_header_x_path)))
                store_header = store.find_element_by_xpath(store_header_x_path)

                try:
                    apologies_ele = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[6]/div/div[2]/div/div/div[3]/form/div[1]/div[1]/div[3]/div/div/p")))
                    apologies_text = apologies_ele.text
                    if str(apologies_text)[0:9] != "Apologies":
                        write_to_file(store_header, state, city)
                    # Testing condition - write to file even if vaccine isn't available
                    else:
                        write_to_file(store_header, state, city)
                except Exception as e:
                    print(e.args)
                    write_to_file(store_header, state, city)

                count += 1
                time.sleep(1)
                break       # comment if you want to look at all locations

        time.sleep(1)
        driver.close()

    except Exception as e:
        print(e.args)


def fill_in_element(id, value, driver, clear=False):
    wait = WebDriverWait(driver, 10)
    ele = wait.until(EC.element_to_be_clickable((By.ID, id)))
    if clear:
        ele.clear()
    ele.click()
    ele.send_keys(value)


def write_to_file(store_header, state, city):
    tz = timezone("EST")
    sg.popup_non_blocking('COVID VACCINE AVAILABLE - check file')

    out_file = open("Available Vaccine Locations", "a")
    out_file.write("\nAs of " + str(datetime.now(tz)) + ": \n")
    out_file.write("COVID-19 vaccine available at " + str(store_header.text) + " in " + str(
        city) + ", " + str(state) + "!\n")
    out_file.close()


def check_states_cities_availability(states_and_cities):
    for state in states_and_cities:
        check_cities_availability(state, states_and_cities[state])


def check_nj_cities_availability(cities, min_interval=None):
    if min_interval is None:
        check_cities_availability("New Jersey", cities)
    else:
        first_loop = True
        start_time = time.time()
        while True:
            if first_loop or (time.time() - start_time)/60 >= min_interval:
                try:
                    check_cities_availability("New Jersey", cities)
                except Exception as e:
                    check_cities_availability("New Jersey", cities)
                start_time = time.time()
                first_loop = False
            else:
                time.sleep(min_interval*60)


min_interval = 5    # Use 'None' if you want to run just once -- or alternatively remove var from method below
cities_to_check = ["08802"]
check_nj_cities_availability(cities_to_check, min_interval)
