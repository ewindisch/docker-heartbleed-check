#!/usr/bin/env python

import datetime
import dockerio.index
import sys
import logging


LOG = logging


##############
MSG_SAFE = """LOW: Probably safe.
This repository is using a distribution / base-image that is known
not to be vulnerable to the Heartbleed bug.

Caution: It is still possible that this image downloads or adds
static binaries or installs the libraries from outside of the
official distribution repositories."""
##############
MSG_PROBABLY_NOT_VULNERABLE = """LOW: Probably not vulnerable.

This repository is running a distribution that was vulnerable,
but a patch has been released and this repository was built following
the release of the Heartbleed patch."""
##############
MSG_VULNERABLE_UNFIXED = """HIGH: Vulnerable.

The repository is running a distribution that is known to
be vulnerable and does not have an official security update.

This image appears to use OpenSSL and thus is presumed to be
highly vulnerable to the Heartbleed attack."""
##############
MSG_UNKNOWN_UNFIXED = """MEDIUM-HIGH: Likely vulnerable.

The repository is running a distribution that is known to
be vulnerable and does not have an official security update.

This tool cannot determine if this repository utilizes OpenSSL
and as such, if the heartbleed vulnerable is relevant to this image.

It is possible that the repository owner is installing a
non-official package or binaries that do not exhibit the Heartbleed
problem.

It is advised that users exercise caution and manually verify
this repository."""
##############
MSG_FIXED_BUT_VULNERABLE = """%s: Vulnerable.

This repository is running a distribution that was vulnerable,
and while a patch has been released, this repository has not
been updated.

It is highly advised that this repository be rebuilt."""
##############
MSG_UNKNOWN_DISTRO = """MEDIUM: Unknown.

The repository is running a distribution that is unknown to
this script.

This tool cannot determine if this repository utilizes OpenSSL
and as such, if the heartbleed vulnerable is relevant to this image.

It is advised that users exercise caution and manually verify
this repository."""
##############


def uses_openssl(dockerfile):
    for line in dockerfile:
        if 'openssl' in line:
            return True
    return False


def has_safe_build_date(repo):
    updated_on = di.get_last_updated(repo)
    updated_on_dt = datetime.datetime.strptime(
        updated_on.split('+')[0], '%Y-%m-%dT%H:%M:%S')

    # Safe distro, but outdated build...
    if updated_on_dt < datetime.datetime(2014, 4, 7):
        return False
    return True


class SafeEnum(object):
    SAFE, FIXED, UNFIXED, UNKNOWN = range(4)


def has_safe_distro(dockerfile):
    for line in dockerfile:
        if line.upper().startswith('FROM'):
            distro = line.split(None)[1]
            tag = None

            if ':' in distro:
                distro, tag = distro.split(':')

            if distro == 'ubuntu':
                if tag and '.' in tag:
                    year, month = map(int, tag.split('.'))
                    if year < 12:
                        if tag in ('11.10', 'oneiric'):
                            return SafeEnum.UNFIXED
                        return SafeEnum.SAFE

                if tag in ('13.04', 'raring',
                           '12.10', 'quantal'):
                    return SafeEnum.UNFIXED

                if tag in (None, 'latest',
                           'trusty', '14.04',
                           'precise', '12.04',
                           'saucy', '13.10'):
                    return SafeEnum.FIXED
            elif distro == 'debian':
                if tag in ('wheezy', 'sid', 'jessie', '7.4', 'latest'):
                    return SafeEnum.FIXED
                else:
                    return SafeEnum.SAFE
    return SafeEnum.UNKNOWN

if __name__ == "__main__":
    repo = sys.argv[1]

    di = dockerio.index.DockerIndex()
    dfs = di.get_dockerfile(repo)
    if not dfs:
        print "Repository not found."
        sys.exit(1)
    dockerfile = dfs.split('\n')

    distro_safety = has_safe_distro(dockerfile)
    if distro_safety == SafeEnum.SAFE:
        print MSG_SAFE
    elif distro_safety == SafeEnum.FIXED:
        # If patched, but running old version...
        if not has_safe_build_date(repo):
            fearlvl = "MEDIUM-HIGH"
            if uses_openssl(dockerfile):
                fearlvl = "HIGH"
            print MSG_FIXED_BUT_VULNERABLE % fearlvl
        else:
            print MSG_PROBABLY_NOT_VULNERABLE
    elif distro_safety == SafeEnum.UNFIXED:
        if uses_openssl(dockerfile):
            print MSG_VULNERABLE_UNFIXED
        else:
            print MSG_UNKNOWN_UNFIXED
    elif distro_safety == SafeEnum.UNKNOWN:
        print MSG_UNKNOWN_DISTRO
