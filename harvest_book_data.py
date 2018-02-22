#!/usr/bin/python3
# -*- coding: utf-8 -*-

from lxml import html
import json
import requests
import sys
import re
from bs4 import BeautifulSoup

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

BASE_URL_DNB = 'https://portal.dnb.de'

QUERY_FORMAT_STRING = BASE_URL_DNB + '/opac.htm?query={0}&method=simpleSearch&cqlMode=true'
QUERY_FORMAT_STRING_2 = BASE_URL_DNB + '/opac.htm?method=showNextResultSite&cqlMode=true&currentResultId={0}%26any&currentPosition={1}'

def get_data_from_book_info (book_data, response, field_name):
    tree = html.fromstring(response.content)
    field_data = tree.xpath('//td/strong[text() = "{}"]/../../td/text()'.format(field_name))
    field_string = ""
    for field in field_data:
        field_string = field_string + field.replace("\n","").replace("\r","").replace("\t","")

    book_data[field_name] = field_string

def get_abstract (book_data, response):
    tree = html.fromstring(response.content)
    link = tree.xpath('//strong[text() = "EAN"]/../..')
    if (len(link) > 0 and len(link[0]) > 1):
        url = "https://www.buchhandel.de/jsonapi/productDetails/" + link[0][1].text.strip()
        page = requests.get(url)
        result = json.loads(page.text)

        if('data' in result): 
            lang = result['data']['attributes']['mainLanguages'][0];
            numberOfAbstracts = len(result['data']['attributes']['mainDescriptions']);
            if(numberOfAbstracts > 0 ):    
                abstract_txt = result['data']['attributes']['mainDescriptions'][0]['description']
        else:
            abstract_txt = ""
            lang = ""

        abstract_txt = cleanhtml(abstract_txt)
        abstract_txt = BeautifulSoup(abstract_txt).get_text();
        
        if(len(abstract_txt) > 0):
            book_data["abstract"]=abstract_txt
            book_data["lang"] = lang
        else:
            book_data["abstract"]=""
    else:
        print("no abstract link")

if __name__ == "__main__":
    book_data = {}
    currentPosition = 0;
    query_string = QUERY_FORMAT_STRING.format("informatik+and+hsg%3D004");
    file_handles = {};
    hFile = open("book_data.json","w+");
    while(True):
        page = requests.get(query_string)
        tree = html.fromstring(page.content)

        links = tree.xpath('//table[@id="searchresult"]//a/@href')

        if(len(links) == 0):
            break;

        for link in links:
            book_info_response = requests.get(BASE_URL_DNB + link)
            get_data_from_book_info(book_data, book_info_response, "Titel")
            get_data_from_book_info(book_data, book_info_response, "EAN")

            get_abstract(book_data, book_info_response)

            for v in book_data.values():             
                print(v.encode('cp850', 'replace').decode('cp850'))
            if(len(book_data["abstract"])>0):
                if book_data["lang"] not in file_handles:
                    file_handles[book_data["lang"]] = open("book_data_" + book_data["lang"] + ".json","w+");
                hFile = file_handles[book_data["lang"]]
                hFile.write(json.dumps(book_data))
                
            hFile.flush();

        query_string = QUERY_FORMAT_STRING_2.format("informatik+and+hsg%3D004",str(currentPosition))
        currentPosition += len(links);
