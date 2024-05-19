# Masterlink Technica Analysis API Handler

This project create an FastAPI bridge to use the Masterlink API.

The api bridge uses FastAPI module and uvicorn as hosting service. Response and namespaces follows RestAPI schemas.


## Installation

Install tech-analysis-api-handler with pip + git

```bash
  pip install git+https://github.com/fighterming/tech-analysis-api-handler.git

```



## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`API_USERNAME` = YOUR_API_USERNAME

`API_PASSWORD` = YOUR_API_PASSWORD

`SQL_URI` = BACKEND_DATABASE_CONNECTOR



## Usage/Examples

Startup of application
```bash
python run.py
```


## API Reference

Namespace: root `http://localhost:8000`      
`GET` /snapshot - testing page.  
`POST` /shutdown - shutdown uvicorn api server.   
`POST` /restart - disconnect from masterlink server and spawn a new api connection.  


Namespace: /ta `http://localhost:8000/ta`  


```http
GET http://localhost:8000/ta/snapshot 
```
`POST` /service - connect  
`PUT` /sub/{symbol} - subscribe to a symbol  
`DELETE` /sub/{symbol}  
`GET` /subs  
`PUT` /ohlc/{symbol}  
`GET` /ohlc/service - get update service status  
`POST` /ohlc/service - update ohlc data  
`DELETE` /ohlc/service - stop ohlc update
`GET` /tick/service - get update service status  
`POST` /tick/service - update tick data  
`DELETE` /tick/service - stop tick data update  