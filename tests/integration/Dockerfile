FROM python:3.14-slim

WORKDIR /tests

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["pytest", "-v", "--tb=short"]
