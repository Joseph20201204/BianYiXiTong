# BianYiXiTong
编译系统-期末大作业

使用方法：

```powershell
python compiler.py <InputFileName>.min [OutputFileName]
```

OutputFileName缺省则命名为InputFileName.*

例：

```powershell
python compiler.py 1.min 测试程序一
python compiler.py 2.min 测试程序二
```

得到结果：

```powershell
Analysis complete. Results in 测试程序一.* files. Total errors: 0
Analysis complete. Results in 测试程序二.* files. Total errors: 5
```

