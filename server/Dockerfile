FROM python:3.11.5
COPY main.py main.py
COPY PermanentMarker-Regular.ttf PermanentMarker-Regular.ttf
ENV AM_I_IN_A_DOCKER_CONTAINER Yes
RUN pip install psycopg2 Pillow flask python-dotenv
CMD ["python", "./main.py"]