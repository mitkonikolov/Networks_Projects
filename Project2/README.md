## High-level Approach
We followed the "Implementing Your Bridge" section of the project assignment page, it gave us a lot of insights and also a point to start. 

We started with first, draw out the networks of each tests on paper, trying ti figure out what is happening and all the different required fields in order to be a valid config file. Started with simple 1 and try to figure out why the starting code will make this test pass.

Once we have a clear understanding of the python starting code and the first few tests, we started coding some implementations and created bridge and message classes, along with their appropriate simple functionalities. We tried to seperate the functionality as much as possible. Then we continue to try and form the spanning tree by sending BPDUs. We tried to think from each bridge's perspective and decide when to open/close a port. Once it is working, we found some bugs and starting to create a port history array.

Once the spanning tree is ready, we started to work on forwarding packets, the forwarding table. We also will update the enabled ports when the BPDUs expired. Lastly, in order to pass some of the advanced tests, we have to add the logic to detect when a bridge gets disconnected from the network, we have to recalculate the spanning tree.

##  Challenged Faced
We have faced a couple challenges during this project, spent a lot of time debugging by drawing out the test case on a white board or reading through the data packets being dropped. The process was slow but they were effective. 

Challenges such as not closing the correct ports was resolved by drawing it on a whiteboard, manually figure out where the root ports are and which are the activated ports. Additionally, sometimes we're seeing tests passing with a sligiht chance for the packets to be dropped. We resolved this issue by comparing the output for the success case and failure case, then the issue become pretty obvious.

## Overview of Testing
Most of the issues we're facing are program correctness, such as having cycles or having duplicated packets. 


* challenged faced 
    - not closing correct ports
        + drew the network on a whiteboard and figure out the correct spanning tree or the activated ports are
    - sometimes work, sometimes doesn't
        + saved the output of the success version and the failed version
            * compared the two files and drew it on a whiteboard
    - having cycles
        + was not closing the ports correctly
    - having issue with duplicated packets
        + played around with the timeing when we receive packets and when we broadcast BPDUs
* overview of testing
    - Correctness
        + going over the program line by line
            * solved the cycle issue
    - Performance
        + when seeing issue with sometimes having duplicate packets
            * wrote a scirpt that will run the test over and over and print out the duplicated message





* high-level approach
    - followed the assignmnte guidelines on the website
    - first draw networks
    - cvreated class for brdige and messages
        + with functionalities
    - creating BPDUs to form the bridge
        + try to seperate the funcitonality as much as possible
        + once it's wokring
        + how to decide which port to close or open
    - started storing port history
        + based on the histroy, deciide hiech port to close nad which to open
    - started identifying data mesage (forwarding table)
        + started having logic for forwarding
        + wrote logic to
            * update enabled ports after BPDUs are expired
    - wrote logic to rebuild spanning tree when bridge is down
