# syntax=docker/dockerfile:1
# Production CI must replace tags with reviewed sha256 digests.
FROM eclipse-temurin:21-jdk AS build
WORKDIR /src
COPY HelloServer.java .
RUN javac --add-modules jdk.httpserver HelloServer.java && \
    jar --create --file app.jar --main-class HelloServer HelloServer.class

FROM eclipse-temurin:21-jre
RUN groupadd --system --gid 10001 app && \
    useradd --system --uid 10001 --gid app --home-dir /nonexistent --shell /usr/sbin/nologin app
WORKDIR /app
COPY --from=build --chown=10001:10001 /src/app.jar /app/app.jar
USER 10001:10001
EXPOSE 8080
ENV PORT=8080
ENTRYPOINT ["java","--add-modules","jdk.httpserver","-XX:MaxRAMPercentage=70","-jar","/app/app.jar"]
