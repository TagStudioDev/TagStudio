# SPDX-FileCopyrightText: (c) TagStudio Contributors
# SPDX-License-Identifier: MIT


def clamp[N: float](value: N, lower_bound: N, upper_bound: N) -> N:
    return max(lower_bound, min(upper_bound, value))
