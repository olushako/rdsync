FROM python:3
ADD script.py /
RUN pip3 install requests
RUN pip3 install schedule
RUN pip3 install PyDrive2
ENTRYPOINT [ "python" , "-u" , "./script.py" ]