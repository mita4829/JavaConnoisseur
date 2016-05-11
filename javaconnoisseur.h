#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NORMAL "\x1B[0m"
#define RED "\x1B[31m"
#define MAGENTA "\x1B[35m"
#define YELLOW "\x1B[33m"
#define GREEN "\x1B[32m"
#define CYAN "\x1B[36m"


const unsigned int pageBuffer = 10000;

struct Object{
    char list[pageBuffer];
    int line[pageBuffer];
    int listsize;
    int linesize;
    int maxSize;
};

struct Object newObject(){
    struct Object token;
    token.linesize = 0; token.maxSize = pageBuffer; token.listsize = pageBuffer; token.maxSize = pageBuffer;
    return token;
}


struct Object parse(struct Object token, char *argv[]){
    char c;
    FILE *js;
    js = fopen(argv[1],"r");
    if(js == NULL){
        printf("%sCannot find file %s.%s\n",YELLOW,argv[1],NORMAL);
        exit(0);
    }
    int i = 0;
    int l = 1;
    while((c = fgetc(js)) != EOF){
        token.list[i] = c;
        token.line[i] = l;
        if(c == '\n'){
            l++;
        }
        i++;
    }
    token.listsize = i;
    token.linesize = i;
    fclose(js);
    return token;
}

struct Object bracket(struct Object token){
    struct Object paren = newObject();
    int j = 0;
    //Create struct that holds only brackets
    for(int i = 0; i < token.listsize; i++){
        if(token.list[i] == '{' || token.list[i] == '}'){
            paren.list[j] = token.list[i];
            paren.line[j] = token.line[i];
            j++;
        }
    }
    paren.listsize = j; paren.linesize = j;
    
    //Loop through and see if there exist an odd number of open/closing brackets
    int high = 0; int count = 0;int index = 0;
    for(int k = 0; k < paren.listsize; k++){
        if(paren.list[k] == '{'){
            count++;
            if(count>high){
                high++;
                index = k;
            }
        }else{
            count--;
        }
    }
    //Missing bracket test
    if(!count){
        printf("%sBracket check: %sPassed!%s\n",CYAN,GREEN,NORMAL);
    }else{
        printf("%sBracket check: %sFailed\n",CYAN,RED);
        printf("%sMissing matching bracket for line: %d%s\n",YELLOW,paren.line[index],NORMAL);
    }
    return paren;
}

//Though modern Javascript does not require the writter to use semi-colons, this tool does in order to tell statements apart.
struct Object semiColon(struct Object token){
    //Create struct that holds all char but whitespace
    struct Object semi = newObject();
    int j = 0;
    for(int i = 0; i < token.listsize; i++){
        if(token.list[i] != ' '){
            semi.list[j] = token.list[i];
            semi.line[j] = token.line[i];
            j++;
        }
    }
    semi.listsize = j;
    semi.linesize = j;
    //Missing semi-colon check
    
    printf("%sSemi-Colon check: ",CYAN);
    int clear = 1;
    for(int i = 0; i<semi.listsize; i++){
        if(semi.list[i] == '\n' && (semi.list[i-1] != '{' && semi.list[i-1] != '}') && (semi.list[i-1] != '\n') && (semi.list[i-1] != ';') && i != 0){
            if(clear == 1){
                printf("%sFailed\n",RED);
                clear = 0;
            }
            printf("%sMissing semi-colon for line: %d%s\n",YELLOW,semi.line[i-1],NORMAL);
        }
    }
    if(clear){
        printf("%sPassed!%s\n",GREEN,NORMAL);
    }
    return semi;
}

//Remove user comments
struct Object noComments(struct Object token){
    struct Object clean = newObject();
    int j = 0, block = 0;
    for(int i = 0; i < token.listsize; i++){
        if((token.list[i] == '/' && token.list[i+1] == '/')){
            //single line comment removal
            block = 1;
        }else if(token.list[i-1] == '\n'){
            block = 0;
        }
        if(!block){
            clean.list[j] = token.list[i];
            clean.line[j] = token.line[i];
            j++;
        }
    }
    clean.listsize = j; clean.linesize = j;
    
    //multi comment line removal
    j = 0; block = 0;
    for(int i = 0; i < clean.listsize; i++){
        if((clean.list[i] == '/' && clean.list[i+1] == '*')){
            block = 1;
        }else if((clean.list[i] == '*' && clean.list[i+1] == '/')){
            clean.list[i] = ' ';
            clean.list[i+1] = ' ';
            block = 0;
        }
        if(block){
            clean.list[i] = ' ';
        }
    }
    return clean;
}

char *getCString(char *argv[]){
    char * buffer = 0;
    long length;
    FILE * js = fopen (argv[1], "r");

    if (js){
        fseek (js, 0, SEEK_END);
        length = ftell (js);
        fseek (js, 0, SEEK_SET);
        buffer = malloc (length);
        if (buffer){
            fread (buffer, 1, length, js);
        }
        fclose (js);
    }
    return buffer;
}

void printSubstring(char str[],int low, int high){
    printf("%s%.*s...\n%s",MAGENTA,high-low+1,(str+low),NORMAL);
}

void dynamicLeaks(char* string){
    const char* New = "new";
    const char* Free = "= null";
    const char* FreeS = "=null";
    const char* newline = "\n";
    const char* ptr; char *index;
    int newCount = 0;
    for(ptr=string;(index=strstr(ptr,New));ptr=index+1){
        newCount++;
    }
    for(ptr=string;(index=strstr(ptr,Free));ptr=index+1){
        newCount--;
    }
    for(ptr=string;(index=strstr(ptr,FreeS));ptr=index+1){
        newCount--;
    }
    
    if(newCount <= 0){
        printf("%sDynamic variables: %sPassed!%s\n",CYAN,GREEN,NORMAL);
    }else{
        printf("%sDynamic variables: %sWarning, recommend terminating variables if not already: %s\n",CYAN,YELLOW,NORMAL);
        int low = 0;
        int high = 0;
        for(ptr=string;(index=strstr(ptr,New));ptr=index+1){
            low = index-string;
            printSubstring(string,low-10,low+8);
        }
    }
}


void print(struct Object token){
    for(int i = 0; i < token.listsize; i++){
        printf("char = %c line= %d\n",token.list[i],token.line[i]);
    }
}
