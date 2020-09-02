from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from time import *
import os
import requests
import threading

separator = "###_###"
options = Options()
options.headless = True
caps = DesiredCapabilities().FIREFOX
caps["pageLoadStrategy"] = "none"
driver = webdriver.Firefox(options=options, capabilities = caps)
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGES_FILE = "images.txt"
CHAPTERS_FILE = "chapters.txt"
MANGA_FILE = "mangas-new.txt"
DONE_FILE = "done"

def load_page(link, timeout, required_id):
    global driver
    driver.get(link)
    sleep(10)
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, required_id))
        )
    finally:
        pass

def get_manga_from_page(link):
    load_page(link, 60, "page")
    mangas = driver.find_elements_by_class_name("comment")
    details = []
    for m in mangas:
        e = m.find_elements_by_tag_name("a")[0]
        l = e.get_attribute("href") + "?abc"
        details.append(l+ separator +e.text)
    return details

def get_images_from_chapter(link):
    image_links = []
    load_page(link, 60, "pic_container")
    pages = len(driver.find_element_by_id("dropdown-menu-page").find_elements_by_tag_name("li"))
    for i in range(pages):
        container = driver.find_element_by_id("pic_container")
        images = container.find_elements_by_tag_name("img")
        for img in images:
            if img.get_attribute("id") == "page"+str(i+1):
                image_links.append(img.get_attribute("src"))
        if i == pages - 1:
            break
        while True:
            try:
                container.click()
                break
            except ElementClickInterceptedException:
                buttons = driver.find_elements_by_tag_name("button")
                buttons[2].click()
                sleep(2)
        sleep(2)
    return image_links

def get_chapters_for_manga(link):
    load_page(link, 60, "chapter_table")
    driver.find_element_by_partial_link_text('click to show').click()
    sleep(1)
    chapter_links = driver.find_element_by_id("chapter_table").find_elements_by_tag_name("a")
    chapters = []
    for c in reversed(chapter_links):
        l = c.get_attribute("href")
        n = c.find_elements_by_tag_name("b")[0].text
        chapters.append(l + separator + n)
    return chapters

def save_to_file(contentArr, filename):
    with open(filename, 'w+') as f:
        f.write('\n'.join(contentArr))

def get_lines_from_file(filename):
    with open(filename) as f:
        content = f.read()
    return content.splitlines()

class DownloadThread(threading.Thread):
    def __init__(self, name, url):
        threading.Thread.__init__(self)
        self.name = name
        self.url = url
    def run(self):
        download(self.url, self.name)

def download(url, name):
    f = requests.get(url, allow_redirects = False)
    open(name, 'wb+').write(f.content)

def download_images(name, num):
    path = BASE_PATH + "/" + name + "/" + num
    image_links = get_lines_from_file(path+"/"+IMAGES_FILE)
    i = 0
    pool_size = 10
    while i<len(image_links):
        j = i+pool_size
        threads = []
        for k in range(i,j):
            if k == len(image_links):
                break
            img = path + "/pic"+str(k+1)+".jpeg"
            threads.append(DownloadThread(img, image_links[k]))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        i = j
    print("download complete for " + name + " " + num)

def download_chapter(name, num, link):
    path = BASE_PATH + "/" + name + "/" + num
    if os.path.exists(path+"/"+DONE_FILE):
        print("done file exists for ", name, num)
        return
    os.mkdir(path)
    images = get_images_from_chapter(link)
    save_to_file(images, path+"/images.txt")
    download_images(name, num)
    open(path+"/"+DONE_FILE, "w+").write("")


def download_chapters(name):
    chapters_file = BASE_PATH + "/" + name + "/" + CHAPTERS_FILE
    chapters = get_lines_from_file(chapters_file)
    for c in chapters:
        download_chapter(name, c.split(separator)[1], c.split(separator)[0])

def download_manga(name, link):
    print("downloading manga "+ name)
    path = BASE_PATH + '/' + name
    if not os.path.isdir(path):
        os.mkdir(path)
    chapters = get_chapters_for_manga(link)
    save_to_file(chapters, path+"/"+CHAPTERS_FILE)
    download_chapters(name)

def download_mangas(start, end):
    manga_links_file = BASE_PATH + "/" + MANGA_FILE
    mangas = get_lines_from_file(manga_links_file)
    for i in range(start, end+1):
        m = mangas[i]
        download_manga(m.split(separator)[1], m.split(separator)[0])

def download_manga_links(start, end):
    links = []
    for i in range(start, end+1):
        print("loading mangas from page ", i)
        link = "http://www.mangago.me/tag/GL/?page="+str(i)
        links.extend(get_manga_from_page(link))
    save_to_file(links, MANGA_FILE)

def download_manga_images(start, end):
    path = BASE_PATH + "/" + MANGA_FILE
    names = get_lines_from_file(path)
    for i in range(start, end+1):
        n = names[i].split(separator)[1]
        path = BASE_PATH + "/" + n
        chapters = get_lines_from_file(path + "/"+CHAPTERS_FILE)
        for c in chapters:
            num = c.split(separator)[1]
            path = BASE_PATH + "/" + n + "/" + num
            if os.path.exists(path+"/"+DONE_FILE):
                print("done file exists for ", n, num)
                continue
            download_images(n, num)
            open(path+"/"+DONE_FILE, "w+").write("")

# download_manga_links(1,1)
# download_mangas(6, 6)
download_manga_images(6,6)

print ("Headless Firefox Initialized")

sleep(5)
driver.quit()