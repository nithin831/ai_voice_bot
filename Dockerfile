FROM python:3.11
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt requirements.txt
COPY voice_chatbot /app
RUN pip3 install -r requirements.txt
RUN python manage.py makemigrations
RUN python manage.py migrate
RUN cd voice_chatbot
EXPOSE 8000
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]