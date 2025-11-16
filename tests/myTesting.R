In <- read.csv("output/ettj_parameters.csv")
View(In[In$grupo_indexador=="PREFIXADOS",])

In <- read.csv("output/ettj_nominal.csv")
View(In[In$du==2520,])
