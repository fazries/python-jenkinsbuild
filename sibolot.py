import sys, getopt
import jenkins
import xml.etree.ElementTree as etree

myuser  = "setyadi.fazrie@totolpelita.com"
mytoken = "8b4d00c679903226a716694e61983dc7"

server  = jenkins.Jenkins('https://jenkins-staging.totolpelita.com/',username=myuser,password=mytoken)


def set_properties(apps_name):
    return """
        pkg_name="""+apps_name +"""
        host_name="""+apps_name +""" 
        apps_name="""+apps_name +"""
        """ 

def set_commands(deployment_type,func):
    if deployment_type == 'go':
        scripts = 'golang'
    if deployment_type == 'node':
        scripts = 'nodejs'

    return"""
    #!/bin/bash

    bash "/share/jenkins-scripts/"""+func+"""/"""+scripts+"""-staging.sh" 
    """ # need to split the env [staging]

def set_pipeline_scripts(deployment_type):
    if deployment_type == 'go':
        scripts = 'golang'
        a = 'goStag'
    if deployment_type == 'node':
        scripts = 'nodejs'
        a = 'nodeStag'

    return""" 
    node(&apos;pipeline&apos;) {
    def """+a+"""= load &apos;/share/jenkins-scripts/pipeline/"""+scripts+"""-staging.groovy&apos;
    """+a+""".doPR(&quot;${git_project}&quot;, &quot;${ghprbPullId}&quot;)
    }

    stage(&quot;Build&quot;) {
        build &apos;Build&apos;
    }

    stage(&quot;Deploy&quot;) {
        build &apos;Deploy&apos;
    }
    """

def set_trigger_phrase(args):
    if args == '':
        return "deploy"
    else:
        return args

def check_job_exist(args):
    return server.get_job_name(args)

def create_job_folder(deployment_type,apps_name):
    xmlfile = 'templates/basetemplate_{}.xml'.format(deployment_type)
    tree = etree.parse(xmlfile)
    root = tree.getroot()

    for dp in root.findall('displayName'):
        dp.text = apps_name.capitalize() 

    config = etree.tostring(root, encoding='utf8', method='xml').decode()
    #print(config)
    jobname = deployment_type+" - "+apps_name
    server.create_job(jobname, config)
    return(True)


def create_job_deploy(deployment_type,apps_name):
    xmlfile ='templates/basetemplate_{}_deploy.xml'.format(deployment_type) 
    tree = etree.parse(xmlfile)
    root = tree.getroot()

    for deploy in root.findall('assignedNode'):
        deploy.text = 'deploy'

    for deploy in root.findall('.//*/command'):
        commands = set_commands(deployment_type,'deploy')  
        deploy.text = commands 

    for deploy in root.findall('.//*/propertiesContent'):
        properties = set_properties(apps_name)
        deploy.text = properties

    config = etree.tostring(root, encoding='utf8', method='xml').decode()
    #print(config) 

    jobname = deployment_type+" - "+apps_name
    server.create_job(jobname+"/Deploy", config)


def create_job_build(deployment_type,apps_name):
    xmlfile ='templates/basetemplate_{}_build.xml'.format(deployment_type) 
    tree = etree.parse(xmlfile)
    root = tree.getroot()

    for build in root.findall('assignedNode'):
        build.text = 'build'
    
    for build in root.findall('.//*/command'):
        commands = set_commands(deployment_type,'build')  
        build.text = commands 

    for build in root.findall('.//*/propertiesContent'):
        properties = set_properties(apps_name)
        build.text = properties

    config = etree.tostring(root, encoding='utf8', method='xml').decode()
    #print(config) 
    jobname = deployment_type+" - "+apps_name
    server.create_job(jobname+"/Build", config)

def create_pipeline(deployment_type,apps_name,admin_list):
    xmlfile = 'templates/basetemplate_{}_pipeline.xml'.format(deployment_type)
    tree = etree.parse(xmlfile)
    root = tree.getroot()

    for pipeline in root.findall('.//*//projectUrl'):
        url = 'https://github.com/totolpelita/'+apps_name+'/'
        pipeline.text = url 
    
    for pipeline in root.findall('.//*/propertiesContent'):
        git_project = apps_name
        pipeline.text = git_project
    
    for pipeline in root.findall('.//*/adminlist'):
        admin = admin_list.split(',')
        pipeline.text = '\n'.join(admin)
   
    for pipeline in root.findall('.//*/triggerPhrase'):
        phrase = set_trigger_phrase('')
        pipeline.text = phrase
    
    for pipeline in root.findall('./definition/script'):
        scripts = set_pipeline_scripts(deployment_type)
        pipeline.text = scripts

    config = etree.tostring(root, encoding='utf8', method='xml').decode()
    #print(config) 
    jobname = deployment_type+" - "+apps_name
    server.create_job(jobname+"/Pipeline", config)

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"h:t:n:a:")
    except getopt.GetoptError:
        print('sibolot.py -t [go] -n [apps_name] -a [admin name]')
        print('usage:')
        print('-t : type of deployment')
        print('-n : name of deployment, should be same with repo')
        print('-a : admin name pipeline')
        print('error')
        sys.exit(2)
    
    itype  = ''
    iname  = ''
    iadmin = []
    for opt, args in opts:
        if opt == '-h' or opt =='--help':
            print('sibolot.py -t [go] -n [apps_name] -a [admin name]')
            print('error')
            sys.exit()
        elif opt in ("-t","--type"):
            itype = args
        elif opt in ("-n","--name"):
            iname = args
        elif opt in ("-a","--admin"):
            iadmin = args

    if itype != '' and iname != '' and len(iadmin) != 0:
        job_type   = itype
        apps_name  = iname
        admin      = iadmin
        deployment_list = ['go','node'] 

        if itype in deployment_list:
            checker = None 
            checker = check_job_exist(apps_name)
            if checker == True:
                print("Job already exist "+apps_name)
                sys.exit()
            else:
                run = create_job_folder(job_type,apps_name)
                if run == True:
                    create_job_build(job_type,apps_name)
                    create_job_deploy(job_type,apps_name)
                    create_pipeline(job_type,apps_name,admin)
                    print("Deployment "+apps_name+" has been created, please check in Jenkins")
    else:
        print('sibolot.py -t [go] -n [apps_name] -a [admin list]')
        print('usage:')
        print('-t : type of deployment')
        print('-n : name of deployment, should be same with repo')
        print('-a : list of admin name')
        print('error')
        sys.exit(2)
        

if __name__ == "__main__":
    main(sys.argv[1:])
