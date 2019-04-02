# Bible MariaDB

Bible MariaDB contains multiple translations of the Holy Bible, as well as cross-references.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY.

### Included Translations
* American Standard-ASV1901 (ASV)
* Bible in Basic English (BBE)
* Darby English Bible (DARBY)
* King James Version (KJV)
* World English Bible (WEB)
* Young's Literal Translation (YLT)
* English Standard Version (ESV)
* New International Version (NIV)
* New Living Translation (NLT)

### Getting Started
```bash
git clone https://www.github.com/rkeplin/bible-mariadb
cd bible-mariadb && docker build -t bible-mariadb .
```

When running a container, all of the environment variables from [MariaDB](https://hub.docker.com/_/mariadb) can be supplied.

### Related Projects
* [Bible PHP API](https://www.github.com/rkeplin/bible-php-api)
* [Bible AngularJS UI](https://www.github.com/rkeplin/bible-angularjs-ui)
* [Bible MariaDB Docker Image](https://www.github.com/rkeplin/bible-mariadb)

### Credits
All of the data was gathered from the MySQL database found [here](https://github.com/scrollmapper/bible_databases).

### License
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/.
