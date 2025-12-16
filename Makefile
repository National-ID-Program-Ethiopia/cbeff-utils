.PHONY: build run test clean docker-build docker-run help

# Default target
help:
	@echo "MOSIP Bio Utils REST Service - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  build         - Build the Java service"
	@echo "  run           - Run the Java service"
	@echo "  test          - Run tests"
	@echo "  clean         - Clean build artifacts"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo "  python-setup  - Setup Python client dependencies"

# Build the service
build:
	mvn clean package

# Run the service
run: build
	java -jar target/bio-utils-rest-service-*.jar

# Run tests
test:
	mvn test

# Clean build artifacts
clean:
	mvn clean
	rm -rf target/

# Build Docker image
docker-build:
	docker build -t bio-utils-service:latest .

# Run Docker container
docker-run:
	docker run -p 8080:8080 bio-utils-service:latest

# Setup Python client
python-setup:
	cd python && pip install -r requirements.txt

