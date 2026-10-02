export const disqualified=row=>['late_submission','no_commits'].includes(row?.status);

export function rankingMarks(reviews,caseId){
  const rows=reviews.filter(r=>!disqualified(r)&&Number.isFinite(r.score)&&(caseId==null||r.caseId===Number(caseId)))
    .sort((a,b)=>b.score-a.score||a.repoId.localeCompare(b.repoId));
  const cutoff=rows[4]?.score;
  let rank=0,last=null;
  return new Map(rows.flatMap((row,index)=>{
    if(last!==row.score){rank=index+1;last=row.score;}
    if(index<5)return [[row.repoId,{kind:'top',rank}]];
    return row.score===cutoff?[[row.repoId,{kind:'reserve',rank}]]:[];
  }));
}

