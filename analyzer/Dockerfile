FROM python:3.11-slim

LABEL maintainer="yjung35@my.bcit.ca"

RUN mkdir /app

# We copy just the requirements.txt first to leverage Docker cache
# on `pip install`
COPY ./requirements.txt /app/requirements.txt

# Set the working directory
WORKDIR /app

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . /app

# Create a non-root user with a known UID/GID
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Set ownership before switching users
RUN chown -R appuser:appgroup /app

# Switch to the new user
USER appuser

# Tells on which port the service listens in the container
EXPOSE 8110

# Entrypoint = run Python
ENTRYPOINT [ "python3" ]

# Default = run app.py
CMD [ "app.py" ]






