#!/usr/bin/python3
# -*- coding: utf-8 -*-

from lxml import html
import requests
import sys

BASE_URL_DNB = 'https://portal.dnb.de'

QUERY_FORMAT_STRING = BASE_URL_DNB + '/opac.htm?method=simpleSearch&query={}'

def get_data_from_book_info (book_data, response, field_name):
    tree = html.fromstring(response.content)
    field_data = tree.xpath('//td/strong[text() = "{}"]/../../td/text()'.format(field_name))
    field_string = ""
    for field in field_data:
        field_string = field_string + field.replace("\n","").replace("\r","").replace("\t","")

    book_data[field_name] = field_string

def get_abstract (book_data, response):
    tree = html.fromstring(response.content)
    link = tree.xpath('//div[@class="news"]//a[@title="Prüfung der Lieferbarkeit bei buchhandel.de"]/@href')
    if (len(link) > 0):
        page = requests.get(link[0])
        tree = html.fromstring(page.content)
        abstract_txt = tree.xpath('//label[substring(text(),1,17) = "Hauptbeschreibung"]')
        print(abstract_txt)
        if(len(abstract_txt) > 0):
            book_data["abstract"]=abstract_txt[0]
        else:
            book_data["abstract"]=""
    else:
        print("no abstract link")

if __name__ == "__main__":
    book_data = {}
    query_string = QUERY_FORMAT_STRING.format("informatik")

    page = requests.get(query_string)
    tree = html.fromstring(page.content)

    links = tree.xpath('//table[@id="searchresult"]//a/@href')

    for link in links:
        book_info_response = requests.get(BASE_URL_DNB + link)
        get_data_from_book_info(book_data, book_info_response, "Titel")
        get_data_from_book_info(book_data, book_info_response, "EAN")

        get_abstract(book_data, book_info_response)

        for v in book_data.values():             
            print(v.encode('cp850', 'replace').decode('cp850'))
