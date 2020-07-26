# Dockerfile
FROM python:3.7-stretch
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV PORT 8080
ENTRYPOINT ["python"]
CMD ["app.py"]
