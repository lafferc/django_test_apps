target_dir = /var/www/html/gamlaffo/

install:
	echo "Installing " `cat VERSION`
	service httpd stop
	pip install -r requirements.txt
	mkdir $(target_dir)
	rsync -rv --exclude=".*" . $(target_dir)
	$(target_dir)/manage.py collectstatic
	$(target_dir)/manage.py migrate
	chown -R apache:apache $(target_dir)
	cp gamlaffo.conf /etc/httpd/conf.d/
	service httpd start

update:
	echo "Upgrading to " `cat VERSION`
	service httpd stop
	pip install -r requirements.txt
	rsync -rv --exclude=".*" . $(target_dir)
	cd $(target_dir); ./manage.py migrate; chown apache:apache *
	service httpd start
