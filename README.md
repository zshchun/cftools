# Codeforces CLI
cf-cli is a unofficial command-line tool for [codeforces](https://codeforces.com).

# Requirement
```
pip install tomli pycryptodome beautifulsoup4
```

# Configuration
Default configuration file is $HOME/.cf-cli/config.[toml](https://toml.io/).

# Usage
## List contests
```
$ cf-cli list
[+] Past contests
...
1695 D2  AB   Codeforces Round #801 (Div. 2) and EPIC  2022-06-18 23:35 (02:00) x22255
1700 D2  AB   Codeforces Round #802 (Div. 2)           2022-06-19 18:05 (02:00) x19157
1696 G   AB   Codeforces Global Round 21               2022-06-25 23:35 (02:15) x23371
1698 D2   B   Codeforces Round #803 (Div. 2)           2022-06-28 23:35 (02:15) x25767
[+] Solved xx contests
```

## List upcoming contests
```
$ cf-cli upcoming
[+] Current or upcoming contests
1699 D2  Codeforces Round #804 (Div. 2)           2022-07-04 23:35 (02:00) 4:23:51
```

# TODO
- [ ] Search editorial link
- [ ] Submit submission
- [ ] Current contest countdown
- [ ] Support user-agent
- [ ] Support RCPC token
- [ ] Support pip
- [ ] Color interface
- [ ] Show streak stats
