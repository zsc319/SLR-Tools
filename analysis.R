# Read 1000 most cited Google Scholar results
GS <- read.csv(file = "GS.csv",header = TRUE,sep = ";")[,c("title","author","year")]
names(GS) <- c("title", "authors","year")
# Read 20000 most cited Scopus results
scopus <- read.csv(file = "scopus.csv",header = TRUE,sep = ",")[,c("Title","Authors","Year")]
names(scopus) <- c("title", "authors","year")
# Read all 29555 Web of Science results
wos <-rbind(read.table("savedrecs-3.txt",header = TRUE,sep = "\t", fill = TRUE, quote = ""),read.table("savedrecs-4.txt",header = TRUE,sep = "\t", fill = TRUE, quote = ""),read.table("savedrecs-5.txt",header = TRUE,sep = "\t", fill = TRUE, quote = ""),read.table("savedrecs-6.txt",header = TRUE,sep = "\t", fill = TRUE, quote = ""),read.table("savedrecs-7.txt",header = TRUE,sep = "\t", fill = TRUE, quote = ""),read.table("savedrecs-8.txt",header = TRUE,sep = "\t", fill = TRUE, quote = ""))[,c("TI","AU","PY")]
names(wos) <- c("title", "authors","year")

full_data <-rbind(GS,scopus,wos)
