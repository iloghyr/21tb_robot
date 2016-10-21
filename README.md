# 21tb 自动挂机学习机器人 
### v1.2

> 适用于时代光华(21tb.com)在线学习系统
> 
> 特别适用于那些强制员工每个月要学习xx学分，学不够扣钱的公司！！
> 
> 注意：本程序帮助你完成挂机的机时，不会答题，如果是课后测试类的，需要最后去完成答题，才能获取学分。
> 
运行环境：python2.7  linux

使用说明：
	
	1、配置你的用户名和公司：main.conf里的 username、password、corpcode
	  其中，corpcode是在线学习21tb配置的合作标识，可以从login页面搜索 "corpCode" 查看隐藏的input标签的值
	2、study.list 里面是保存需要挂机学习的课程id，需要在课程中心手动选择，比如本月需要学习12个学分，在课程中心里可以选两个6学分的课程，课程的ID可以从url的参数标识中获取
	3、如何获取课程的ID
	例如：http://xxx.21tb.com/els/html/courseStudyItem/courseStudyItem.learn.do?courseId=LIV01004_fjnx.com.cn&vb_server=&willGoStep=COURSE_COURSE_STUDY
	课程ID为courseId参数的值，加到study.list中，一个课程一行
	4、开始学习
		python study_robot.py
		或者
		nohup python study_robot.py 2>&1 > runtime.log &
		
## 示例
	
![示例](https://raw.githubusercontent.com/iloghyr/21tb_robot/master/demo.png)
