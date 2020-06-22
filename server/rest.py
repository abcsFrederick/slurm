from bson import ObjectId
import os
from subprocess import Popen, PIPE

from girder import events
from girder.api.rest import Resource
from girder.api.describe import Description, autoDescribeRoute
from girder.api import access
from girder.constants import AccessType, TokenScope
from . import event_handlers
import datetime


class Slurm(Resource):
    def __init__(self):
        super(Slurm, self).__init__()
        self.resourceName = 'slurm'

        self.route('GET', (), self.getSlurm)
        self.route('PUT', ('cancel', ':id'), self.cancelSlurm)
        self.route('POST', (), self.submitSlurmJob)
    # Find link record based on original item ID or parentId(to check chirdren links)
    # Return only record that have READ access(>=0) to user.
    # @access.user(scope=TokenScope.DATA_READ)
    @access.public
    @autoDescribeRoute(
        Description('Search for segmentation by certain properties.')
        .notes('You must pass a "parentId" field to specify which parent folder'
               'you are searching for children folders and items segmentation information.')
        .errorResponse()
        .errorResponse('Read access was denied on the parent resource.', 403)
    )
    def getSlurm(self):
        hostname = ''
        res = Popen(['squeue'], stdout=PIPE, stderr=PIPE)
        for line in res.stdout:
            line = line.rstrip()
            print(line)
        return res.stdout

    @access.public
    @autoDescribeRoute(
        Description('Search for segmentation by certain properties.')
        .notes('You must pass a "parentId" field to specify which parent folder'
               'you are searching for children folders and items segmentation information.')
        .errorResponse()
        .errorResponse('Read access was denied on the parent resource.', 403)
    )
    def cancelSlurm(self):
        res = Popen(['scancel',''], stdout=PIPE, stderr=PIPE)
        retcode = res.wait()
        while not retcode:
            retcode = res.wait()

    @access.public
    @autoDescribeRoute(
        Description('Search for segmentation by certain properties.')
        .notes('You must pass a "parentId" field to specify which parent folder'
               'you are searching for children folders and items segmentation information.')
        .errorResponse()
        .errorResponse('Read access was denied on the parent resource.', 403)
    )
    def submitSlurmJob(self):
        script = '''#!/bin/bash
                    for (( i=60; i>0; i--)); do
                      sleep 1 &
                      printf " $i \n"
                      wait
                    done
                 '''
        with open('', "w") as sh:
            sh.write(script)
        print sh.name
        res = Popen(['sbatch',sh.name])
        for line in res.stdout:
            line = line.rstrip()
            print(line)
        return res.stdout
