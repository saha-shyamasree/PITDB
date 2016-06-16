import re
import locale

from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy.sql import func, distinct
from sqlalchemy import desc
from pit_app.models import *
from pit_app import db


results = Blueprint('results',  __name__)

@results.route('/tge')
def tge():
  # Get the argument - accession
  accession = request.args['accession']

  # Find the TGE for the given accession number
  tge        = TGE.query.filter_by(accession=accession).one()
  tgeObs     = Observation.query.filter_by(tge_id=tge.id).order_by(desc(Observation.peptide_num))
  obsCount   = tgeObs.count()
  organisms  = Observation.query.with_entities(Observation.organism).filter_by(tge_id=tge.id).distinct(Observation.organism).all()
  tgeClasses = Observation.query.with_entities(Observation.tge_class).filter_by(tge_id=tge.id).distinct(Observation.tge_class).all()
  uniprotIDs = Observation.query.with_entities(Observation.uniprot_id).filter_by(tge_id=tge.id).distinct(Observation.uniprot_id).all()
  
  pepLengths = Peptide.query.with_entities(func.length(Peptide.aa_seq).label('pepLength')).\
                    join(TgeToPeptide, Peptide.id == TgeToPeptide.peptide_id).\
                    join(Observation,  Observation.id == TgeToPeptide.obs_id).\
                    join(TGE, TGE.id == Observation.tge_id ).\
                    filter_by(id=tge.id).\
                    group_by(Peptide.aa_seq).all() 

  avgPeptNum = Observation.query.with_entities(func.avg(Observation.peptide_num).label('average')).one()

  # avgPeptCov = len(tge.amino_seq) / (pepLengthSum)

  # Flatten out the list of lists to lists (to use in the for loops)
  organisms  = [item for sublist in organisms for item in sublist]
  tgeClasses = [item for sublist in tgeClasses for item in sublist]
  uniprotIDs = [item for sublist in uniprotIDs for item in sublist]
  pepLengths = [item for sublist in pepLengths for item in sublist]

  summary    = { 'tge' : tge, 'tgeObs' : tgeObs, 'organisms' : organisms, 'avgPeptNum' : avgPeptNum.average, 
                  'tgeClasses' : tgeClasses, 'obsCount' : obsCount, 'uniprotIDs': uniprotIDs, 
                  'avgPeptCov': float(len(tge.amino_seq))/sum(pepLengths) };

  results  = []

  for obs in tgeObs:

    sample = Sample.query.filter_by(id=obs.sample_id).first()
    exp    = Experiment.query.filter_by(id=sample.exp_id).first()
    #transc = Transcript.query.filter_by(obs_id=obs.id).first()
    tgePep = TgeToPeptide.query.filter_by(obs_id=obs.id).all()
    tgeType    = re.search("(?<=type:).*?(?=\s)", obs.long_description).group(0)
    tgeLength  = re.search("(?<=len:).*?(?=\s)",  obs.long_description).group(0)
    tgeStrand  = re.search("(?<=\().*?(?=\))",    obs.long_description).group(0)
    peptides = set()

    for peptide in tgePep: 
      pept = Peptide.query.filter_by(id=peptide.peptide_id).first()
      peptides.add(pept.aa_seq)

    results.append({'id': obs.id, 'observation': obs.name, 'sample': sample.name, 'experiment': exp.title, 
      'type': tgeType, 'length': tgeLength, 'strand':tgeStrand, 'organism': obs.organism, 'uniprotID': obs.uniprot_id,
  		'peptide_num': obs.peptide_num, 'peptides': list(peptides)})

  return render_template('results/tge.html', summary = summary, results=results)


@results.route('/organism')
def organism():
  tgeList = []

  organism   = request.args['organism']
  obs        = Observation.query.filter_by(organism=organism)

  # tgeClasses is to be used in the modal window
  #tgeClasses = Observation.query.with_entities(distinct(Observation.tge_class)).filter_by(organism=organism).all()
  #tgeClasses = [item for sublist in tgeClasses for item in sublist]

  tges       = TGE.query.join(Observation).filter_by(organism=organism).distinct(Observation.tge_id).all()
  tgeNum     = separators(obs.distinct(Observation.tge_id).count())
  sampleNum  = separators(obs.join(Sample).distinct(Sample.id).count())
  expNum     = separators(obs.join(Sample).join(Experiment).distinct(Experiment.id).count())

  trnNum    = separators(Transcript.query.join(Observation, Transcript.obs_id == Observation.id).\
                    filter(Observation.organism==organism).distinct().count())

  pepNum    = separators(Observation.query.with_entities(func.sum(Observation.peptide_num)).\
                    filter_by(organism=organism).scalar())

  summary = {'organism': organism,'tgeNum': tgeNum, 'sampleNum': sampleNum, 'expNum': expNum, 'trnNum': trnNum, 'pepNum' : pepNum };
  
  for tge in tges: 
    tgeClasses = Observation.query.with_entities(Observation.tge_class).filter_by(tge_id = tge.id).all()
    uniprotIDs = Observation.query.with_entities(Observation.uniprot_id).filter_by(tge_id = tge.id).all()

    tgeClasses = [item for sublist in tgeClasses for item in sublist]
    uniprotIDs = [item for sublist in uniprotIDs for item in sublist]

    tgeList.append({'accession': tge.accession, 'tgeClasses': tgeClasses, 'uniprotIDs':uniprotIDs }) #  })
  
  return render_template('results/organism.html', summary = summary, tgeList= tgeList)


@results.route('/experiment')
def experiment():
  experiment  = request.args['experiment']

  exp  = Experiment.query.filter_by(id=experiment).first_or_404()
  user = User.query.with_entities(User.fullname).filter_by(id=exp.user_id).one()

  samples   = Sample.query.filter_by(exp_id=experiment).all()
  sampleNum = Sample.query.filter_by(exp_id=experiment).distinct().count()

  obsNum = separators(Observation.query.join(Sample, Observation.sample_id==Sample.id).\
        join(Experiment, Experiment.id==Sample.exp_id ).\
        filter(Experiment.id==experiment).distinct().count())

  tgeNum = separators(TGE.query.join(Observation, TGE.id == Observation.tge_id).\
        join(Sample, Observation.sample_id==Sample.id).\
        join(Experiment, Experiment.id==Sample.exp_id ).\
        filter(Experiment.id==experiment).distinct(Observation.tge_id).count()) #distinct() -- removed distinct for now

  trnNum = separators(Transcript.query.join(Observation, Transcript.obs_id == Observation.id).\
        join(Sample, Observation.sample_id==Sample.id).\
        join(Experiment, Experiment.id==Sample.exp_id ).\
        filter(Experiment.id==experiment).distinct().count())

  pepNum = separators(Observation.query.with_entities(func.sum(Observation.peptide_num)).\
        join(Sample, Observation.sample_id==Sample.id).\
        join(Experiment, Experiment.id==Sample.exp_id ).\
        filter(Experiment.id==experiment).scalar())

  summary = {'id': experiment,'title': exp.title, 'user': user.fullname, 'sampleNum': sampleNum, 'tgeNum' : tgeNum, 'obsNum' : obsNum, 'trnNum' : trnNum, 'pepNum' : pepNum};
   
  sampleList = []

  for sample in samples:
    tgePerSample = Observation.query.filter(Observation.sample_id==sample.id).distinct(Observation.tge_id).count()
    sampleList.append({'id':sample.id, 'name': sample.name, 'tgeNum': separators(tgePerSample) })

  return render_template('results/experiment.html', summary = summary, sampleList = sampleList)


@results.route('/protein')
def protein():
  uniprot  = request.args['uniprot']

  obs  = Observation.query.with_entities(distinct(Observation.organism)).filter_by(uniprot_id=uniprot).all()
  organism = [item for sublist in obs for item in sublist]
  organism = ''.join(organism)

  tges = TGE.query.join(Observation).filter_by(uniprot_id=uniprot).\
              distinct(Observation.tge_id)

  tgeList = []

  # for tge in tges:
  #   tgePerSample = Observation.query.filter(Observation.tge_id==tge.id).all()
  
  #   tgeList.append({'accession':sample.id, 'name': sample.name, 'tgeNum':tgePerSample })

  return render_template('results/protein.html', tges = tges, uniprot = uniprot, organism = organism)


@results.route('/aminoseq')
def aminoseq():  
  tgeList = []
  
  # Get the two arguments searchData and searchType (exact or partial)
  searchData = request.args['searchData']
  searchType = request.args['searchType']

  if searchType == 'exact':
    # We expect only one match for one particular aminoseq
    tge = TGE.query.filter(TGE.amino_seq == searchData).one()
    return redirect(url_for('results.tge', accession = tge.accession))

  else:
    tges = TGE.query.filter(TGE.amino_seq.like("%"+searchData+"%")).all()

    for tge in tges: 
      # For each TGE get the obs num, organisms, uniprotID and tgeClass
      obsNum     = Observation.query.filter_by(tge_id=tge.id).count()
      organisms  = Observation.query.with_entities(Observation.organism).filter_by(tge_id=tge.id).distinct(Observation.organism).all()
      tgeClasses = tge.tge_class
      uniprotIDs = tge.uniprot_id
      
      # Flatten out the list of lists to lists (to use in the for loops)
      organisms  = [item for sublist in organisms for item in sublist]
      
      sampleNum = Sample.query.with_entities(Sample.name).\
                      join(Observation, Observation.sample_id == Sample.id).\
                      filter_by(tge_id=tge.id).\
                      distinct(Sample.name).count()

      tgeList.append({ 'accession': tge.accession, 'length': len(tge.amino_seq), 'obsNum': obsNum, 
        'organisms': organisms, 'tgeClasses': tgeClasses,  'uniprotIDs': uniprotIDs, 'sampleNum': sampleNum })

  return render_template('search/results.html', tgeList = tgeList)


@results.route('/peptide/<peptide>')
def peptide(peptide):
  return render_template('results/peptide.html')

@results.route('/transcript/<transcript>')
def transcript(transcript):
  return render_template('results/transcript.html')

def separators( inputText ):
  locale.setlocale(locale.LC_ALL, 'en_US')
  newText = locale.format("%d", inputText, grouping=True)
  return newText

