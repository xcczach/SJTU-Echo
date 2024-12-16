# https://blog.csdn.net/weixin_51238373/article/details/140383863

if command -v sudo &>/dev/null; then
    SUDO="sudo"
else
    SUDO=""
fi

# Install Chrome
wget -N https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.108/linux64/chrome-linux64.zip 
unzip chrome-linux64.zip
chmod +x chrome-linux64/chrome
${SUDO} ln -s $(pwd)/chrome-linux64/chrome /usr/bin/google-chrome
# Remove zip file
rm chrome-linux64.zip

# Install Chrome Driver
wget -N https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.108/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
chmod +x chromedriver-linux64/chromedriver
${SUDO} ln -s $(pwd)/chromedriver-linux64/chromedriver /usr/bin/chromedriver
# Remove zip file
rm chromedriver-linux64.zip