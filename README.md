# pytest-easyread

This is a pytest plugin that aims to make the way pytest reports to terminal easier to read.

### Requirements

You will need the following prerequisites in order to use pytest-easyread:  

Python (tested on versions 2.7 and 3.4)
pytest 3.0.4 or newer  


### Installation

To install pytest-easyread:  

```
$ pip install pytest-easyread
```

Then add --easy flag when you run the tests, like this:
```
$ pytest --easy
 ```

 ### Ideal use

 - pytest-easyread is optimised for use with tests names that use underscores, like "test_this_feature_works"  
 - For now pytest-easyread is set to verbose mode only  
