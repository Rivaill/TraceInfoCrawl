# TraceInfoCrawl
> A python3 script to assist TraceView in its use,For crawling the information(lable,abi) needed by TraceView.

For additional information see the TraceView FAQ.  
About TraceView:  a pure front-end evm trace visualization tool, URL:
[https://traceview.tofreedom.me/](https://traceview.tofreedom.me/)

## Step 1
Fill Raw traces into **rawtraces.txt** file
```shell
vim rawtraces.txt
```

## Step 2
Install dependency packages
```shell
pip install -r requirements.txt
```

## Step3
Run the script to see the instructions
```shell
python main.py
```
Output
```
Raw traces fill to rawtraces.txt
And run e.g. : 
python main.py "https://etherscan.io/address/ADDRESSFLAG#code"
The script parameters provide the URL of the Blockchain Explorer's contract code page ,through which to crawl to the required information.
ADDRESSFLAG is a variable representing an address, similar to a placeholder, which will be replaced by the actual address at runtime
```
Run command according to this


## Step4
Paste the Address map and Function map from the script output into TraceView
![](./screenshot.jpg)
