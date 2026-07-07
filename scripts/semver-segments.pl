#!/usr/bin/env perl
# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: CC0-1.0

use strict;
use warnings;
use feature 'say';

# From: https://regex101.com/r/vkijKf/1
if (($ARGV[0] // <STDIN>) =~ /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/) {
    foreach my $index (0 .. $#{^CAPTURE}) {
        say ${^CAPTURE}[$index] // "";
    }
}
