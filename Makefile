target_dir = /var/www/html/gamlaffo/

update
     echo "Upgrading to " `cat VERSION`
     service httpd stop
     pip install requirements.txt
     rsync -rv --exclude=".*" . $(target_dir)
     cd $(target_dir)
     ./manage.py migrate
     chown apache:apache *
     service httpd start
