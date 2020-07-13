FROM osgeo/gdal:ubuntu-small-latest
# FROM osgeo/gdal:alpine-ultrasmall-latest
# FROM osgeo/gdal:alpine-normal-latest

WORKDIR "/app"

COPY ./requirements.txt ./

# RUN apk add curl
RUN apt-get --assume-yes install python3-distutils
RUN apt-get --assume-yes install libglib2.0-0
RUN apt-get --assume-yes install libsm6
RUN apt-get --assume-yes install libxrender1
RUN apt-get --assume-yes install libxext6
RUN apt-get --assume-yes install zip
RUN apt-get --assume-yes install unzip
RUN apt-get --assume-yes install p7zip-full p7zip-rar

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py

# RUN apt-get install curl
RUN pip install -r requirements.txt

COPY . .

# RUN unzip './data/sample.zip' -d ./data
RUN cd ./data && p7zip -d sample.7z 

CMD ["python", "index.py"]
