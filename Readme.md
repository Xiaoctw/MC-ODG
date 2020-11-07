# MC-ODG
Oversample the specified data set by entering a command on the command line.
The data set has been processed by feature project and is in the "data" folder.
The oversampled data is saved in the 'resampled_data' folder.
The following is an optional dataset:
```
datasets = ['adult', 'automobile', 'breast-cancer-wisconsin', 'ecoli',
            'glass', 'haberman', 'transfusion', 'transfusion', 'wine', 'yeast']
```
An example of the program running is given below:
```
 python3 oversample.py -dataset yeast -eps 0.13 -min_pts 3 -fit_outline_radio True -outline_radio 0.2 -noise_radio 0.7
```
The log is as follows:
```
INFO:root:Data reading completed
INFO:root:Number of core production points :19, number of boundary production points :14, number of noise production points :0
INFO:root:Number of core production points :163, number of boundary production points :54, number of noise production points :0
INFO:root:Number of core production points :212, number of boundary production points :86, number of noise production points :0
INFO:root:Number of core production points :168, number of boundary production points :240, number of noise production points :0
INFO:root:Number of core production points :377, number of boundary production points :38, number of noise production points :0
INFO:root:Number of core production points :317, number of boundary production points :109, number of noise production points :0
INFO:root:Number of core production points :311, number of boundary production points :77, number of noise production points :43
INFO:root:Data oversampling is completed
INFO:root:Data written to file completed
```