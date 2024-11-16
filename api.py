# Pufferfish API

#-------------#
#   IMPORTS   #
#-------------#

import os
from dotenv import load_dotenv
from typing import Annotated
from fastapi import Body,FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


#------------------------#
#   INITIALIZE FASTAPI   #
#------------------------#

# Creates FastAPI App
app = FastAPI() 
origins = ["*"]

# Allows cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)                                                   


#---------------------#
#   INITIALIZE APIS   #
#---------------------#

load_dotenv() # Loads environment variables from a .env file if present for local development


#-----------------#
#   DATA MODELS   #
#-----------------#

# Define any data models here


#-------------------#
#   HELPER METHODS  #
#-------------------#

# Insert any helper methods here


#---------------#
#   ENDPOINTS   #
#---------------#

# Sanity check endpoint to ensure server is accessible
@app.get("/")
async def sanity_check():
    return {
        "message": "Welcome to the Pufferfish API! To read more about the available endpoints, visit https://ADD API URL HERE/docs"
    }

