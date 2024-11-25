# adapted from https://www.geeksforgeeks.org/how-to-install-selenium-in-python/

wget https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-linux64.tar.gz
tar -xvzf geckodriver*
chmod +x geckodriver
sudo mv geckodriver /usr/local/bin/
rm geckodriver*
sudo apt-get install firefox