import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel
import json






class City:
    def __init__(self, city, address, cities, generative_api_key):
        self.city = city
        self.address = address
        self.cities = cities
        os.environ["GOOGLE_API_KEY"] = generative_api_key
        pass


    def get_city_code(self):
        city_code = cityExtractor(cities=self.cities, city=self.city, address=self.address)
        if city_code:
            return city_code
        return False







class Extraction(BaseModel):
    isDetrmined: bool
    cityCode: int



def cityExtractor(cities, city, address):

    messages = [
    SystemMessage(
        f"""
            OBJECTIVE

            your job is to recive city and address user has entered and extract the city code

            CONTEXT

            you helping the custommer support to detrmined the city code user mean
            cities {cities}

            if you can not detrmined the city ot it unclear or not in the citys list you should return isDetrmined false and cityCode None
            use the city first if it does not provide the solution use the address
        
            
        """
    ),

    HumanMessage(f"city : {city} \n address: {address}")
    ]

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash").with_structured_output(Extraction)

    result = llm.invoke(messages).model_dump()

    if result["isDetrmined"] == False:
        return False
    return result["cityCode"]
