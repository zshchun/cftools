# Codeforces CLI
Codeforces CLI is a unofficial command-line tool for [codeforces](https://codeforces.com).

# Installation
```
pip3 install cftools
```

# Configuration
Default configuration file is $HOME/.cf/config.[toml](https://toml.io/).

# Usage
## List contests
```
$ cf list
[+] Past contests
...
1695 D2  2/6 Codeforces Round #801 (Div. 2) and EPIC  2022-06-18 23:35 (02:00) x22255
1700 D2  2/6 Codeforces Round #802 (Div. 2)           2022-06-19 18:05 (02:00) x19157
1696 G   2/8 Codeforces Global Round 21               2022-06-25 23:35 (02:15) x23371
1698 D2  2/7 Codeforces Round #803 (Div. 2)           2022-06-28 23:35 (02:15) x25767
[+] Solved 4/300 contests
```

## List upcoming contests
```
$ cf upcoming
[+] Current or upcoming contests
1704 D12 CodeTON Round 2 (Div. 1 + Div. 2, Rated, 2022-07-31 23:05 (02:30) 05d+22:11
1714 D3  Codeforces Round #811 (Div. 3)           2022-08-01 23:35 (02:15) 06d+22:41
1713 D2  Codeforces Round (Div. 2)                2022-08-06 23:35 (02:00) 11d+22:41
```

## Login
```
$ cf login
[+] Login account
Input handle or email: handle
Password:
```

## Search editorial link
```
$ cf editorial
```

## View submission
```
$ cf solution
```

## Submit source code
```
$ cf submit
```

## Open contest link
```
$ cf open 1698
```

# TODO
- [x] Search editorial link
- [x] Submit submission
- [ ] Race contest
- [ ] Support user-agent
- [x] Support cookies
- [ ] Support RCPC token
- [x] Support pip
- [x] Color interface
- [ ] Show streak stats
- [ ] Clear databases/cache
- [ ] Support multiplatform
- [ ] Support languages
- [ ] Problem parser
- [x] Login
