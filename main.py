from dnacentersdk import api
import datetime
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", help="DNA Center API Username", required=True)
parser.add_argument("-p", "--password", help="DNA Center API Password", required=True)
parser.add_argument('-s','--servers', nargs='+', help='List of servers seperated by a space', required=True)
parser.add_argument("-d", "--devicetemplate", help="The device series, as represented in GH folders (eg. 9300L)", required=True)
args = parser.parse_args()

log_name = datetime.datetime.now()
log_name = log_name.strftime("%d%b%y" + "-" "%H" + "." + "%M")

logger = logging.getLogger(__name__)

# Stream Handler
stream = logging.StreamHandler()
streamformat = logging.Formatter("%(levelname)s:%(module)s:%(lineno)d:%(message)s")
stream.setLevel(logging.DEBUG)
stream.setFormatter(streamformat)

# Adding all handlers to the logs
logger.propagate = False
logger.addHandler(stream)


def main(args):
    status = False
    with open(args.devicetemplate + "/BASE.jinja") as f:
        config_template = f.readlines()
        config_template = "".join(config_template)

    for server in args.servers:
        dnac = dnac_connector(server, args.username, args.password)
        project_id = get_dnac_project(dnac)
        template_id = False

        while not project_id[0]["templates"]:
            logger.critical(server + "template_id was not retrieved from the server, re-creating the template")
            create_dnac_template(dnac, config_template, project_id)
            project_id = get_dnac_project(dnac)
            status = True

        while not template_id:
            for template in project_id[0]["templates"]:
                if template["name"] == "BASE":
                    template_id = template["id"]

        if not status:
            logger.info(server + "updating template with the ID of" + template_id)
            update_dnac_template(dnac, config_template, template_id, project_id)
            status = True

        result = dnac.configuration_templates.version_template(templateId=template_id, comments="Sync from GitHub Repo at " + str(datetime.datetime.now()))
        logger.critical(server + ":  Task complete, ID: " + str(result["response"]["taskId"]))
def dnac_connector(base_url, user, password):
    dnac = api.DNACenterAPI(base_url=base_url,
                            username=user, password=password, verify=False)
    return dnac


def create_dnac_template(dnac, config_template, project):
    dnac.configuration_templates.create_template(
        language="JINJA",
        name="BASE",
        project_id=project[0]["id"],
        softwareType="IOS-XE",
        deviceTypes=[{'productFamily': 'Switches and Hubs', 'productSeries': 'Cisco Catalyst 9300 Series Switches'}],
        templateContent=str(config_template)
    )
    return 200


def update_dnac_template(dnac, config_template,template_id, project):
    dnac.configuration_templates.update_template(
        id=template_id,
        name="BASE",
        language="JINJA",
        project_id=project[0]["id"],
        softwareType="IOS-XE",
        deviceTypes=[{'productFamily': 'Switches and Hubs', 'productSeries': 'Cisco Catalyst 9300 Series Switches'}],
        templateContent=config_template
    )
    return 200


def get_dnac_project(dnac):
    project_id = dnac.configuration_templates.get_projects("Day0 9300L Templates")
    return project_id


if __name__ == "__main__":
    main(args)

    """
    
    LOGGING MATRIX:
                        This logging level will display logs from the categories in the rows
                        info    warning     debug   critical    error   
    logger.info          X                    X
    logger.warning       X         X          X
    logger.debug                              X
    logger.critical      X         X          X        X          X
    logger.exception     X         X          X                   X
    logger.error         X         X          X                   X

    debug is most verbose,
    info is 2nd most verbose
    warning is 3rd most verbose
    error is 4th most verbose
    critical is the least verbose

    """

    """
    API Error Codes:
    200 - OK
    404 - Not Found
    """