FROM python:3.12-slim

#image of the docker
WORKDIR /app

#install the requirements in the docker
COPY requirements.txt . 

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# local port 
EXPOSE 8000

#command to deploy the docker local
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

