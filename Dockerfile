FROM python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 WE_SPEAK_DATA=/data
WORKDIR /app
COPY app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home forum && mkdir /data && chown forum:forum /data
COPY app/ ./
RUN WE_SPEAK_DEV=1 python manage.py collectstatic --noinput && chown -R forum:forum /app /data && chmod 700 /data /data/upload-tmp
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["python", "entrypoint.py"]
