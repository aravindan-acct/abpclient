#! /usr/bin/python3

import requests
import scrapy
from bs4 import BeautifulSoup
import re
import os
from scrapy_client import BlogSpider
import json
import getpass
from http_basic_auth import generate_header, parse_header
try: 
    import queue
except ImportError:
    import Queue as queue
from queue import Queue
from concurrent.futures import ThreadPoolExecutor,as_completed
import sys
from statistics import mean

def contents():
    print('''
    
    What test do you want to perform ? \n
    1:  Execute a simple get request 10 times to a web application \n
    2.  Crawl the site \n
    3.  Find the input params of a web page form \n
    4.  Tarpit Test

    ''')
    try:
        selection = input("Select the required option: ")
    except KeyboardInterrupt:
        exit(0)
    return selection

def start_over():

    start_over_option=input('''
    

    Want to start over ? Enter "YES" to start over or "NO" to exit the script: ''')
    try:
        if start_over_option == "YES":
            main()
        elif start_over_option == "NO":
            exit(0)
        else:
            print("wrong input, exiting...")
    except KeyboardInterrupt:
        exit(0)

def define_web_app():
    os.system('clear')
    print('''
    ********************************************************************
    * This tool should be used for demonstration purposes only. Please *
    * get the customer's permission before running the tool on any of  *
    * their web applications.                                          *
    ********************************************************************
    ''')
    try:
        name=input("Enter the web app URL, for example, 'https://google.com/': ")
        return name
    except KeyboardInterrupt:
        exit(0)

def simple_get(web_app_url):
    r=requests
    total_req=list()
    for i in range (0,10):
        try:
            print(f"URL : { web_app_url } ")
            new_request=r.get(web_app_url)
            if new_request.status_code == 200:
                print(f"{i} The request is successful: {new_request.status_code} and the response time is { new_request.elapsed.total_seconds()}")
                total_req.insert(0,"ok")
                total_req.insert(0,new_request.elapsed.total_seconds())  
            else:
                print(f"{i} The request was not successful: {new_request.status_code} and the response time is { new_request.elapsed.total_seconds()}")
                total_req.insert(0,"request failed")
                total_req.insert(0,new_request.elapsed.total_seconds())
        except:
            print(f"Connection failed\n")
            result="conn failed"
            total_req.insert(0,result)
    return total_req

def tarpit_test(web_app_url):
    concurrent = 100
    data1=list()
    #q=queue.Queue(concurrent * 3)
    q=queue.Queue()
    def task():
        while True:
            url=q.get()
            stats=simple_get(url)
            q.task_done()
            stats_queue.put(stats)
            get_elements=stats_queue.get()
            return get_elements
    try:
        for i in range (0,concurrent):
            q.put(web_app_url)
    except KeyboardInterrupt:
        sys.exit(1)
    stats_queue=queue.Queue()
    with ThreadPoolExecutor() as executor:
        results=[executor.submit(task) for _ in range(concurrent)]
        for result in results:
            data=result.result()
            data1.insert(0,data)
    stats=list()
    def removenesting(data1):
        for i in data1:
            if type(i)==list:
                removenesting(i)
            else:
                stats.append(i)
        return stats
    removenesting(data1)
    print(f"Successful Requests: {stats.count('ok')}")
    print(f"Failed Requests: {stats.count('request failed')}")
    print(f"Connections dropped: {stats.count('conn failed')}")
    for _ in stats:
        if 'ok' in stats:
            stats.remove('ok')
        elif 'request failed' in stats:
            stats.remove('request failed')
        elif 'conn failed' in stats:
            stats.remove('conn failed')
    print(f"Avg Response Time for the requests: { mean(stats)} seconds ")

            

def crawler_func(web_app_url):
    start_url=input("What is the start URL: ")
    crawl_url=web_app_url+start_url
    response=requests.get(crawl_url)
    page_html=response.text
    soup=BeautifulSoup(page_html,'lxml')
    hrefs=soup.findAll('a')
    return hrefs

def recursive_crawler(web_app_url):
    hrefs=crawler_func(web_app_url)
    list_of_urls=list()
    for href in hrefs:
        url=href.attrs.get('href')
        list_of_urls.append(url)
    print(f'''Index of the crawled URL Space: \n
    {list_of_urls}
    ''')
    for url in list_of_urls:
        try:
            response=requests.get(web_app_url+url, timeout=5)
        except:
            print(f"Error saving { url }")
            pass
        file_name=url.replace("/","")
        file=open(file_name,"w+")
        file.write(response.text)
        file.close()
        print(f"Saving { file_name }")
        file.__exit__
    start_over()
    return 0
            
def cred_tester(web_app_url):
    url_space=input("Enter the URI Space for the credential test, for example, cgi-bin/login.cgi :  ")
    complete_url=web_app_url+url_space
    print(f"Checking the parameters for the URL: {complete_url}")
    response=requests.get(complete_url)
    page_html=response.text
    soup=BeautifulSoup(page_html, 'lxml')
    input_params=soup.find_all('input')
    print("Input parameters are: \n\n")
    for txt in input_params:
        print(txt)
        print("\n")
    '''forms=soup.find_all('form')
    print("Forms are: \n\n")
    for txt in forms:
        print(forms)
        print("\n")'''
    start_over()

def waf_login():
    requests.packages.urllib3.disable_warnings()
    waf_ip=input("What is the WAF's management ip(Typically the WAN IP): ")
    waf_login_passwd=getpass.getpass("\nWAF login password: ")
    print("\nConnecting to the WAF on port 8443 as 'admin'...")
    waf_url="https://"+waf_ip+":8443/restapi/v3.1/login"
    headers={"Content-Type": "application/json"}
    payload={"username":"admin","password":waf_login_passwd}
    token_req_json=requests.post(waf_url, data=json.dumps(payload), headers=headers, verify=False)
    token_output=token_req_json.text
    token_split=token_output.split(":")
    token_rstrip=token_split[1].rstrip("}")
    token=token_rstrip.replace('"','')
    auth_header=generate_header('',token)
    payload_headers={"Content-Type":"application/json", "Authorization": auth_header}
    return waf_ip, waf_login_passwd, payload_headers

def waf_get_logs(ip,passwd,headers):
    print('''
    1. Access Logs
    2. Audit Logs
    3. Network Firewall Logs
    4. System Logs
    5. Web Firewall Logs
    ''')
    log_types={"access-logs":"1", "audit-logs":"2", "network-firewall-logs":"3", "system-logs":"4","web-firewall-logs":"5"}
    log_type_input=input("Log Type: ")
    for key, value in log_types.items():
        try:
            if log_type_input == value:
                log_url="https://"+ip+":8443"+"/restapi/v3.1/logs/"+key
                logs_request=requests.get(log_url,headers=headers,verify=False)
                logs_output=json.dumps(logs_request.text, ensure_ascii=False, indent=3)
                print(logs_output)
        except KeyboardInterrupt:
            exit(0)

def main():
    os.system('clear')
    print("\n\nChoose 1 for querying the WAF for service information or logs \n\n")
    print("Choose 2 for testing the ABP settings \n")
    choice=input("What do you want to do: ")
    if choice == "1":
        waf_ip,waf_passwd,token=waf_login()
        waf_get_logs(waf_ip,waf_passwd,token)

    elif choice == "2":
        web_app_url=define_web_app()
        selection=contents()
        try:
            if selection == "1":
                simple_get(web_app_url)
            elif selection == "2":
                recursive_crawler(web_app_url)
            elif selection == "3":
                cred_tester(web_app_url)
            elif selection == "4":
                tarpit_test(web_app_url)

        
            else:
                print("wrong selection")
                exit(0)
        except KeyboardInterrupt:
            exit(0)

if __name__ == '__main__':
    main()

