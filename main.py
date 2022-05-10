# -*- coding: UTF-8 -*-
import json
import logging
import re
import sys
import time
import requests
from web3._utils.abi import normalize_event_input_types
from web3.auto import w3

HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.44'}



def crawl4byte(hex_signature,fourbytes_api="https://www.4byte.directory/api/v1/signatures/?hex_signature=SIGFLAG"):
    print(hex_signature)
    try:
        res = requests.get(fourbytes_api.replace("SIGFLAG", hex_signature),headers=HEADERS, timeout=60)
        if "text_signature" in res.text and len(res.json()["results"])>0:
            return res.json()["results"][-1]["text_signature"]
    except Exception as e:
        logging.exception(e)

    try:
        github_4byte = "https://raw.githubusercontent.com/ethereum-lists/4bytes/master/signatures/SIGFLAG"
        res = requests.get(github_4byte.replace("SIGFLAG", hex_signature),headers=HEADERS, timeout=60)
        if res.status_code==200:
            return res.text

    except Exception as e:
        logging.exception(e)

def crawlExplorer(addrs,explorer_url):
    etherscan_lable_pattern = re.compile(r"title='Public Name Tag \(viewable by anyone\)'>(.*?)</span>")
    etherscan_token_pattern = re.compile(r'Tracker Page">(.*?)</a>')
    etherscan_contractname_pattern = re.compile(r'Contract Name:[\s\S]*?>(.*?)</span>')
    etherscan_abi_pattern = re.compile(r'js-copytextarea2.*?>(.*?)</')

    blockscout_token_pattern = re.compile(r'token_hash_link.*?>(.*?)</a>')
    blockscout_contractname_pattern = re.compile(r'Contract name:.*?>[\s\S].*?>(.*?)</dd>')
    blockscout_abi_pattern = re.compile(r'data-clipboard-text="(.*?)"\s*aria-label="Copy Contract ABI')



    addrs_len = len(addrs)
    index = 0
    lables = {}
    abis = []
    while index < addrs_len:
        print(addrs[index])
        try:
            res = requests.get(explorer_url.replace("ADDRESSFLAG", addrs[index]), headers=HEADERS, timeout=60)

            search_result = re.search(etherscan_abi_pattern, res.text)
            if search_result:
                abis.append(search_result.group(1))
            else:
                search_result = re.search(blockscout_abi_pattern, res.text)
                if search_result:
                    abis.append(search_result.group(1).replace("&quot;", '"'))

            search_result = re.search(etherscan_lable_pattern, res.text)
            if search_result:
                lables[addrs[index]] = search_result.group(1)
            else:
                search_result = re.search(etherscan_token_pattern, res.text)
                if search_result:
                    lables[addrs[index]] = search_result.group(1).replace("<span>","").replace("</span>","")
                else:
                    search_result = re.search(etherscan_contractname_pattern, res.text)
                    if search_result and "Contract Creation Code" in res.text:
                        lables[addrs[index]] = search_result.group(1)
                    else:
                        search_result = re.search(blockscout_token_pattern, res.text)
                        if search_result:
                            lables[addrs[index]] = search_result.group(1)
                        else:
                            search_result = re.search(blockscout_contractname_pattern, res.text)
                            if search_result:
                                lables[addrs[index]] = search_result.group(1)

            index += 1
        except Exception as e:
            logging.exception(e)
            time.sleep(5)
    return lables, abis

def abi_to_interface(abi):
    interface = "function {fn_name}({fn_input})".format(
        fn_name=abi['name'],
        fn_input=','.join([
            arg['type']+" "+arg['name'] for arg in normalize_event_input_types(abi.get('inputs', []))
        ]),
    )
    if len(abi.get('outputs', []))>0:
        interface+= " returns ({fn_returns})".format(
            fn_returns=','.join([
                arg['type']+" "+arg['name'] for arg in normalize_event_input_types(abi.get('outputs', []))
            ])
        )
    return interface


def main(explorer_url):
    raw_traces = open('rawtraces.txt').read()
    raw_traces = raw_traces.startswith("[") and raw_traces or "[" + raw_traces
    raw_traces = raw_traces.endswith("]") and raw_traces or raw_traces + "]"
    raw_traces = json.loads(raw_traces)

    addrs = []
    funcsigs = []

    func_interface = {}

    for trace in raw_traces:
        from_addr = trace["action"].get("from","")
        to_addr = trace["action"].get("to","")
        if not to_addr and trace["action"].get("init",""):
            to_addr = trace["result"].get("address", "")

        if to_addr not in addrs:
            addrs.append(to_addr)
        if from_addr not in addrs:
            addrs.append(to_addr)

        if len(trace["action"].get("input","")) >= 10:
            if trace["action"]["input"][:10] not in funcsigs:
                funcsigs.append(trace["action"]["input"][:10])

    (addr_lable, abis) = crawlExplorer(addrs,explorer_url)


    for funcsig in funcsigs:
        for abi in abis:
            temp_contrct = w3.eth.contract(address="0x0000000000000000000000000000000000000000", abi=abi)
            try:
                temp_contrct.get_function_by_selector(funcsig)
                func_interface[funcsig] = abi_to_interface(temp_contrct.get_function_by_selector(funcsig).abi)
            except ValueError:
                pass

        if not func_interface.get(funcsig,""):
            text_signature = crawl4byte(funcsig)
            if text_signature:
                func_interface[funcsig] = "function "+text_signature


    addr_lable_json = json.dumps(addr_lable,indent=4)
    func_interface_json = json.dumps(func_interface,indent=4)
    print('--------------------Address map--------------------')
    print(addr_lable_json)
    open('address_map.txt','w').write(addr_lable_json)
    print('Save in file: address_map.txt')

    print('--------------------Function map--------------------')
    print(func_interface_json)
    open('function_map.txt','w').write(func_interface_json)
    print('Save in file: function_map.txt')


if __name__ == '__main__':
    if len(sys.argv)!=2:
        print('Raw traces fill to rawtraces.txt')
        print('And run e.g. : ')
        print('python main.py "https://etherscan.io/address/ADDRESSFLAG#code"')
        print("The script parameters provide the URL of the Blockchain Explorer's contract code page ,through which to crawl to the required information.")
        print('ADDRESSFLAG is a variable representing an address, similar to a placeholder, which will be replaced by the actual address at runtime')
    else:
        main(sys.argv[1])
