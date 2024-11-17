FROM python:3.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./mock_data /code/mock_data

CMD ["fastapi", "run", "app/api.py", "--port", "8080"]
