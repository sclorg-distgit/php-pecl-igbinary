# centos/sclo spec file for php-pecl-igbinary, from:
#
# remirepo spec file for php-pecl-igbinary
# with SCL compatibility, from:
#
# Fedora spec file for php-pecl-igbinary
#
# Copyright (c) 2010-2019 Remi Collet
# License: CC-BY-SA
# http://creativecommons.org/licenses/by-sa/4.0/
#
# Please, preserve the changelog entries
#
%if 0%{?scl:1}
%global sub_prefix sclo-%{scl_prefix}
%if "%{scl}" == "rh-php70"
%global sub_prefix sclo-php70-
%endif
%if "%{scl}" == "rh-php71"
%global sub_prefix sclo-php71-
%endif
%if "%{scl}" == "rh-php72"
%global sub_prefix sclo-php72-
%endif
%if "%{scl}" == "rh-php73"
%global sub_prefix sclo-php73-
%endif
%scl_package       php-pecl-igbinary
%endif

%global extname    igbinary
%global ini_name   40-%{extname}.ini

Summary:        Replacement for the standard PHP serializer
Name:           %{?sub_prefix}php-pecl-igbinary
Version:        2.0.8
Release:        2%{?dist}
Source0:        http://pecl.php.net/get/%{extname}-%{version}.tgz
License:        BSD
Group:          System Environment/Libraries

URL:            http://pecl.php.net/package/igbinary

BuildRequires:  %{?scl_prefix}php-pear
BuildRequires:  %{?scl_prefix}php-devel >= 5.2.0
BuildRequires:  %{?scl_prefix}php-pecl-apcu-devel
BuildRequires:  %{?scl_prefix}php-json

Requires:       %{?scl_prefix}php(zend-abi) = %{php_zend_api}
Requires:       %{?scl_prefix}php(api) = %{php_core_api}

Provides:       %{?scl_prefix}php-%{extname}                = %{version}
Provides:       %{?scl_prefix}php-%{extname}%{?_isa}        = %{version}
Provides:       %{?scl_prefix}php-pecl(%{extname})          = %{version}
Provides:       %{?scl_prefix}php-pecl(%{extname})%{?_isa}  = %{version}
%if "%{?scl_prefix}" != "%{?sub_prefix}"
Provides:       %{?scl_prefix}php-pecl-%{extname}           = %{version}-%{release}
Provides:       %{?scl_prefix}php-pecl-%{extname}%{?_isa}   = %{version}-%{release}
%endif

%if 0%{?fedora} < 20 && 0%{?rhel} < 7
# Filter shared private
%{?filter_provides_in: %filter_provides_in %{_libdir}/.*\.so$}
%{?filter_setup}
%endif


%description
Igbinary is a drop in replacement for the standard PHP serializer.

Instead of time and space consuming textual representation, 
igbinary stores PHP data structures in a compact binary form. 
Savings are significant when using memcached or similar memory
based storages for serialized data.

Package built for PHP %(%{__php} -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;')%{?scl: as Software Collection (%{scl} by %{?scl_vendor}%{!?scl_vendor:rh})}.


%package devel
Summary:       Igbinary developer files (header)
Group:         Development/Libraries
Requires:      %{name}%{?_isa} = %{version}-%{release}
Requires:      %{?scl_prefix}php-devel%{?_isa}

Provides:      %{?scl_prefix}php-%{extname}-devel         = %{version}-%{release}
Provides:      %{?scl_prefix}php-%{extname}-devel%{?_isa} = %{version}-%{release}
%if "%{?scl_prefix}" != "%{?sub_prefix}"
Provides:      %{?scl_prefix}php-pecl-%{extname}-devel         = %{version}-%{release}
Provides:      %{?scl_prefix}php-pecl-%{extname}-devel%{?_isa} = %{version}-%{release}
%endif

%description devel
These are the files needed to compile programs using Igbinary


%prep
%setup -q -c

mv %{extname}-%{version} NTS

%{?_licensedir:sed -e '/COPYING/s/role="doc"/role="src"/' -i package.xml}

cd NTS

# Check version
subdir="php$(%{__php} -r 'echo PHP_MAJOR_VERSION;')"
extver=$(sed -n '/#define PHP_IGBINARY_VERSION/{s/.* "//;s/".*$//;p}' src/$subdir/igbinary.h)
if test "x${extver}" != "x%{version}%{?prever}"; then
   : Error: Upstream version is ${extver}, expecting %{version}%{?prever}.
   exit 1
fi
cd ..

cat <<EOF | tee %{ini_name}
; Enable %{extname} extension module
extension=%{extname}.so

; Enable or disable compacting of duplicate strings
; The default is On.
;igbinary.compact_strings=On

; Use igbinary as session serializer
;session.serialize_handler=igbinary

; Use igbinary as APC serializer
;apc.serializer=igbinary
EOF


%build
cd NTS
%{_bindir}/phpize
%configure --with-php-config=%{_bindir}/php-config
make %{?_smp_mflags}


%install
rm -rf %{buildroot}

make install -C NTS INSTALL_ROOT=%{buildroot}

install -D -m 644 package.xml %{buildroot}%{pecl_xmldir}/%{name}.xml

install -D -m 644 %{ini_name} %{buildroot}%{php_inidir}/%{ini_name}

# Test & Documentation
cd NTS
for i in $(grep 'role="test"' ../package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 $i %{buildroot}%{pecl_testdir}/%{extname}/$i
done
for i in $(grep 'role="doc"' ../package.xml | sed -e 's/^.*name="//;s/".*$//')
do install -Dpm 644 $i %{buildroot}%{pecl_docdir}/%{extname}/$i
done


%check
MOD=""
# drop extension load from phpt
sed -e '/^extension=/d' -i ?TS/tests/*phpt

# APC required for test 045
if [ -f %{php_extdir}/apcu.so ]; then
  MOD="-d extension=apcu.so"
fi
if [ -f %{php_extdir}/apc.so ]; then
  MOD="$MOD -d extension=apc.so"
fi

: simple NTS module load test, without APC, as optional
%{_bindir}/php --no-php-ini \
    --define extension=%{buildroot}%{php_extdir}/%{extname}.so \
    --modules | grep %{extname}

# Json used in tests
if [ -f %{php_extdir}/json.so ]; then
  MOD="$MOD -d extension=json.so"
fi

: upstream test suite
cd NTS
TEST_PHP_EXECUTABLE=%{_bindir}/php \
TEST_PHP_ARGS="-n $MOD -d extension=%{buildroot}%{php_extdir}/%{extname}.so" \
NO_INTERACTION=1 \
REPORT_EXIT_STATUS=1 \
%{_bindir}/php -n run-tests.php --show-diff


# when pear installed alone, after us
%triggerin -- %{?scl_prefix}php-pear
if [ -x %{__pecl} ] ; then
    %{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
fi

# posttrans as pear can be installed after us
%posttrans
if [ -x %{__pecl} ] ; then
    %{pecl_install} %{pecl_xmldir}/%{name}.xml >/dev/null || :
fi

%postun
if [ $1 -eq 0 -a -x %{__pecl} ] ; then
    %{pecl_uninstall} %{extname} >/dev/null || :
fi


%files
%{?_licensedir:%license NTS/COPYING}
%doc %{pecl_docdir}/%{extname}
%config(noreplace) %{php_inidir}/%{ini_name}
%{php_extdir}/%{extname}.so
%{pecl_xmldir}/%{name}.xml


%files devel
%doc %{pecl_testdir}/%{extname}
%{php_incldir}/ext/%{extname}


%changelog
* Fri Oct 25 2019 Remi Collet <remi@remirepo.net> - 2.0.8-2
- build for sclo-php72

* Mon Oct 22 2018 Remi Collet <remi@remirepo.net> - 2.0.8-1
- update to 2.0.8

* Wed Jun 27 2018 Remi Collet <remi@remirepo.net> - 2.0.7-1
- update to 2.0.7

* Mon May 14 2018 Remi Collet <remi@remirepo.net> - 2.0.6-1
- update to 2.0.6

* Mon Nov  6 2017 Remi Collet <remi@remirepo.net> - 2.0.5-1
- update to 2.0.5

* Thu Aug 10 2017 Remi Collet <remi@remirepo.net> - 2.0.4-2
- change for sclo-php71

* Mon Apr 24 2017 Remi Collet <remi@remirepo.net> - 2.0.4-1
- update to 2.0.4

* Thu Apr 13 2017 Remi Collet <remi@fedoraproject.org> - 2.0.3-1
- update to 2.0.3
- tarball generated from github (not yet available on pecl)

* Thu Dec 29 2016 Remi Collet <remi@fedoraproject.org> - 2.0.1-1
- cleanup for SCLo build

* Tue Dec 20 2016 Remi Collet <remi@fedoraproject.org> - 2.0.1-1
- Update to 2.0.1

* Thu Dec  1 2016 Remi Collet <remi@fedoraproject.org> - 2.0.0-2
- rebuild with PHP 7.1.0 GA

* Mon Nov 21 2016 Remi Collet <remi@fedoraproject.org> - 2.0.0-1
- update to 2.0.0 (php 5 and 7, stable)

* Tue Oct 18 2016 Remi Collet <remi@fedoraproject.org> - 1.2.2-0.6.20161018git6a2d5b7
- refresh with sources from igbinary instead of old closed repo igbinary7

* Wed Sep 14 2016 Remi Collet <remi@fedoraproject.org> - 1.2.2-0.5.20160724git332a3d7
- rebuild for PHP 7.1 new API version

* Mon Jul 25 2016 Remi Collet <remi@fedoraproject.org> - 1.2.2-0.4.20160724git332a3d7
- refresh

* Sat Jul 23 2016 Remi Collet <remi@fedoraproject.org> - 1.2.2-0.3.20160715gita87a993
- ignore 1 test with 7.1

* Mon Jul 18 2016 Remi Collet <remi@fedoraproject.org> - 1.2.2-0.2.20160715gita87a993
- refresh, newer snapshot

* Wed Mar  2 2016 Remi Collet <remi@fedoraproject.org> - 1.2.2-0.1.20151217git2b7c703
- update to 1.2.2dev for PHP 7
- ignore test results, 4 failed tests: igbinary_009.phpt, igbinary_014.phpt
  igbinary_026.phpt and igbinary_unserialize_v1_compatible.phpt
- session support not yet available

* Fri Jun 19 2015 Remi Collet <remi@fedoraproject.org> - 1.2.1-2
- allow build against rh-php56 (as more-php56)
- drop runtime dependency on pear, new scriptlets

* Wed Dec 24 2014 Remi Collet <remi@fedoraproject.org> - 1.2.1-1.1
- Fedora 21 SCL mass rebuild

* Fri Aug 29 2014 Remi Collet <remi@fedoraproject.org> - 1.2.1-1
- Update to 1.2.1

* Thu Aug 28 2014 Remi Collet <remi@fedoraproject.org> - 1.2.0-1
- update to 1.2.0
- open https://github.com/igbinary/igbinary/pull/36

* Sun Aug 24 2014 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.11.git3b8ab7e
- improve SCL stuff

* Wed Apr  9 2014 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.10.git3b8ab7e
- add numerical prefix to extension configuration file

* Wed Mar 19 2014 Remi Collet <rcollet@redhat.com> - 1.1.2-0.9.git3b8ab7e
- fix SCL dependencies

* Fri Feb 28 2014 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.8.git3b8ab7e
- cleanups
- move doc in pecl_docdir
- move tests in pecl_testdir (devel)

* Sat Jul 27 2013 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.6.git3b8ab7e
- latest snapshot
- fix build with APCu

* Fri Nov 30 2012 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.3.git3b8ab7e
- cleanups

* Sat Mar 03 2012 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.2.git3b8ab7e
- macro usage for latest PHP

* Mon Nov 14 2011 Remi Collet <remi@fedoraproject.org> - 1.1.2-0.1.git3b8ab7e
- latest git against php 5.4
- partial patch for https://bugs.php.net/60298
- ignore test result because of above bug

* Sat Sep 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-2
- use latest macro
- build zts extension

* Mon Mar 14 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- version 1.1.1 published on pecl.php.net
- rename to php-pecl-igbinary

* Mon Jan 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-2
- allow relocation using phpname macro

* Mon Jan 17 2011 Remi Collet <rpms@famillecollet.com> 1.1.1-1
- update to 1.1.1

* Fri Dec 31 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-3
- updated tests from Git.

* Sat Oct 23 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-2
- filter provides to avoid igbinary.so
- add missing %%dist

* Wed Sep 29 2010 Remi Collet <rpms@famillecollet.com> 1.0.2-1
- initital RPM

