#! /usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django.conf import settings
import requests
import jsonpickle
import json
import os

import parse


# @cache_page(60 * 60)
def home(request):
    query = request.GET.get('q', "Java sleep milliseconds")
    context = _getSearchResponse(query)
    return render(request, 'skim/index.html', context)


# @cache_page(60 * 60)
def search(request):
    query = request.GET.get('q', "Java sleep milliseconds")
    context = _getSearchResponse(query)
    return HttpResponse(jsonpickle.encode(context, unpicklable=False), content_type="application/json")


# @cache_page(60 * 60)
def tutorial(request):
    answers = json.load(open(os.path.join(
        settings.STATIC_ROOT, "skim/data/write_answers_201412010847.json"
    )))
    parsedAnswers = parse.parseAnswers(answers)
    context = {
        'query': "write to file",
        'answers': jsonpickle.encode(parsedAnswers, unpicklable=False),
        'questions': [],
        'skipQuestionSelect': True,
    }
    return render(request, 'skim/index.html', context)


def _getSearchResponse(query):
    questionUrl = 'https://api.stackexchange.com/2.2/search/advanced'

    questions = requests.get(questionUrl, params={
        'order': 'desc',
        'sort': 'relevance',
        'q': query,
        'site': 'stackoverflow',
        'pagesize': '20',           # No of Questions
        'tagged': 'java',
        'filter': '!9YdnSK0R1',
        }).json()

    parsedQuestions = parse.parseQuestions(questions)

    questionIds = ';'.join(str(q.id_) for q in parsedQuestions);
    answerUrl = 'https://api.stackexchange.com/2.2/questions/' + str(questionIds) + '/answers'
    moreAnswers = True
    pageNumber = 1
    allAnswers = {'items': []}
    while moreAnswers:
        answers = requests.get(answerUrl, params={
            'order': 'desc',
            'sort': 'votes',
            'site': 'stackoverflow',
            'page': pageNumber,
            'pagesize': '100',           # No of Answers
            'filter': '!b0OfNZ*ohL7Iue',
            }).json()
        moreAnswers = answers['has_more']
        pageNumber += 1
        allAnswers['items'].extend(answers['items'])
    print "Pages: " + str(pageNumber - 1)
    print "Answers: " + str(len(allAnswers['items']))
    parsedAnswers = parse.parseAnswers(allAnswers)

    return {
        'query': query,
        'answers': jsonpickle.encode(parsedAnswers, unpicklable=False),
        'questions': jsonpickle.encode(parsedQuestions, unpicklable=False), 
    }
