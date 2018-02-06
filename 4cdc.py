#!/usr/bin/python
import urllib.request
import urllib.error
import urllib.parse
import argparse
import os
import re
import time
import http.client 
import fileinput
import time
import itertools
import multiprocessing
from multiprocessing import Pool
from multiprocessing import Process
import lxml.html
from bs4 import BeautifulSoup
import django

workpath = os.path.dirname(os.path.realpath(__file__))
regexForFileLinks = '(\/\/is\d*\.4chan\.org/\w+\/(\d+\.(?:jpg|png|gif|webm)))'

def load(url):
    req = urllib.request.Request(url, headers={'User-Agent': '4chan Browser'})
    return urllib.request.urlopen(req).read()

def main():
    fname = "linklist.txt"
    with open(fname,'a+') as f: #opens file for reading and apending (creates the file if it doesnt exist)
        f.seek(0,0)
        threadlinks = f.readlines()
    threadlinks = [line.strip() for line in threadlinks]
    threadlinks = [line for line in threadlinks if line[:4].lower() == 'http']

    if threadlinks == [] or len(threadlinks) == 0:
        print("put the links to threads into the linklist.txt file, one link per line")

    print("::: Downloading " + str(len(threadlinks)) + " Threads\n")
    j = 1
    for threadlink in threadlinks:
        print("::: Downloading Thread " + str(j) + "/" + str(len(threadlinks)))
        j = j + 1
        download_thread(threadlink)

def process_url(directory, link_img_tuple, index):
    link = link_img_tuple[0]
    img = link_img_tuple[1]
    img_path = os.path.join(directory, img)
    if not os.path.exists(img_path):
        start_time = time.time()
        urllib.request.urlretrieve('https:' + link, img_path)
        timeelapsed = time.time() - start_time
        filesize = ((os.stat(img_path).st_size) / (1024 * 1024))
        kbs = str(round(((filesize * 1024) / timeelapsed)))
        print(index + " ::: " + str(round(filesize, 1)) + "MB @ " + kbs + " kilobyte/second")
    else:
        print(index + " exists - skipping")

def getThreadTitle(soup):
        titles = [element.text for element in soup.find_all("span", "subject")]
        title = max(titles, key=len)
        threadTitleFiltered = re.sub("[^ 0-9a-zA-Z]+", "", title)[:45]
        return threadTitleFiltered

def getThumbnailLink(soup):
        a = soup.find("a", {"class":"fileThumb"}) #get first a with class filethumb
        img = a.find("img")                       # get tag img of a
        return img.get("src")                   # get attribute src of tag img

def mkdirs(thread_link, soup):
        threadTitle = getThreadTitle(soup)
        board = thread_link.split('/')[3]
        title2 = soup.title.string.split(' - ')[1]
        threadID = thread_link.split('/')[5].split('#')[0]

        if len(threadTitle) <= 0:
            threadTitle = (threadID + '_' + title2)[:45]

        directory = os.path.join(workpath, 'downloads', board, threadTitle.strip())
        if not os.path.exists(directory):
            os.makedirs(directory)

        return directory

def createListForStatusDisplay(list_of_url_filename):
        indexlist = range(1,len(list_of_url_filename) + 1)
        list2 = list(map(str, indexlist))
        mystring = "/" + str(len(list_of_url_filename))
        list3 = [s + mystring for s in list2]
        return list3

def getFileLinkList(soup):
        linklist = [link['href'] for link in soup.find_all('a',{"class":"fileThumb"}, href=True)]
        fnames = [os.path.basename(link) for link in linklist]
        
        return list(zip(linklist,fnames))

def download_thread(thread_link):
    try:
        loadedthread = load(thread_link).decode("utf-8")
        soup = BeautifulSoup(loadedthread,"lxml")
        directory = mkdirs(thread_link, soup)
        
        #urllib.request.urlretrieve("http:" + getThumbnailLink(soup), directory + "\\thumb.jpg") # stupid me didnt know windows makes thumbnails of webm anyways :/
        while True:
            try:
                list_of_url_filename = list(set(re.findall(regexForFileLinks, loadedthread)))
                list_of_url_filename = getFileLinkList(soup)
                pool = multiprocessing.Pool(processes=6)
                pool.starmap(process_url, zip(itertools.repeat(directory), list_of_url_filename, createListForStatusDisplay(list_of_url_filename)))

            except (urllib.error.URLError, http.client.BadStatusLine, http.client.IncompleteRead):
                time.sleep(20)
                continue

            break
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass