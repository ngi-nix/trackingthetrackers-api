# TODOs

- [ ] marhsalling of FileEntry to JSON ResponseModel object and vice versa
- [ ] make a module out of malware_cache
- [ ] unittests for everything
- [ ] combine unittests with CI
- [ ] docstrings everywhere
- [ ] make DB replaceable : redis as an option
- [ ] write a developer guide
- [ ] improve file checks (e.g. is it really an APK file? Can we unzip it? , etc...)

- [ ] performance tests + graph results
- [ ] load tons of samples into DB

- [ ] combine with analysis engine


# Testing

- [ ] test if installation procedure works

# Speed

- [ ] Currently we execute b"SELECT contains_malware, contains_trackers, contains_adware from cache WHERE sha256 = '239e856979cf26ac999a83bd94d1984a38d65a7dcc6022c83ede2f97b937d60f'" three times. Optimize.

# Nice to haves

- [ ] (maybe?) re-think the Cache and Entry architecture: use SQLAlchemy?



