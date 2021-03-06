import React, {useState} from "react";
import Resolution from "../../elastic/model/Resolution";
import {PersonAnn} from "../../elastic/model/PersonAnn";
import {joinJsx} from "../../util/joinJsx";
import {Profile} from "./Profile";
import {PersonType} from "../../elastic/model/PersonType";

type AttendantProps = {
  resolution: Resolution,
  markedIds: number[]
}

type StateType = {
  show: boolean,
  person?: number
}

export function AttendantsInfo(props: AttendantProps) {
  const r = props.resolution;

  const [state, setState] = useState({
    show: false,
  } as StateType);

  async function toggle(i: number) {
    const personAnn = r.people[i];
    if (personAnn.id === state.person) {
      setState({...state, show: !state.show});
      return;
    }
    setState({...state, person: personAnn.id, show: true});

  }

  const p = state.person;

  return <>
    <div className="accordion mb-2">
      <div className="card">
        <div className="card-header attendants-card">

          <small><strong>Aanwezigen:</strong> {r.people.length ? r.people
            .sort(presidentFirst)
            .filter(isAttendant)
            .map(
              (a: PersonAnn, i: number) =>
                <button className={'btn btn-link ' + highlightMarked(a)} onClick={() => toggle(i)} key={i}>
                  {a.name}{a.president ? ' (president)' : ''}
                </button>
            ).reduce(joinJsx) : '-'}
          </small>
        </div>
        {p ?
          <div className={`collapse ${state.show ? 'show' : 'hide'}`}>
            <div className="card-body">
              <Profile person={p}/>
            </div>
          </div>
          : null}
      </div>
    </div>
  </>;

  function isAttendant(p: PersonAnn) {
    return p.type === PersonType.ATTENDANT;
  }

  function presidentFirst(a: PersonAnn, b: PersonAnn) {
    return a.president ? -1 : b.president ? 1 : 0;
  }

  function isMarked(p: any) {
    return props.markedIds.includes(p.id);
  }

  function highlightMarked(a: any) {
    return isMarked(a) ? 'highlight' : '';
  }

}
