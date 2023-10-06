import styles from '../styles/Home.module.css';
import { useState, useEffect, useRef } from 'react';

const Ninjas = () => {

  const [msg_name, setMsg_name] = useState("")
  const [canData, setCanData] = useState([])
  const [instanceBtn, setInstanceBtn] = useState([])
  const [flag, setFlag] = useState(false)
  const [flagInstance, setflagInstance] = useState(true)
  const [instanceFilter, setInstanceFilter] = useState("")
  const [componentData, setcomponentData] = useState({})
 
  const prevCanRef = useRef();

  const callApi = async () => {
    const res = await fetch("http://localhost:8001/can_ui")
    const data = await res.json();
    return{
      props: {components: data}
    }
  }

  function getComponentData(name){
    let result = canData.filter(can => {
      return can[name]
    })
    return result   
  }

  useEffect(() => {

    Array.isArray(instanceBtn) ? null: setcomponentData(instanceBtn[msg_name])
    }, [instanceBtn]);

  useEffect(() =>{
    prevCanRef.current = componentData
    Object.keys(componentData).length > 0 ? setFlag(true): null
  }, [componentData])

  useEffect(() => {

    if (msg_name){
      let data = getComponentData(msg_name)
      setcomponentData(data[0][msg_name])
    }
    
    if (flag && instanceBtn["instances"].length > 0){
      
      let onChange = canData.filter(can => {
        return can[instanceBtn["name"]]
      })

      if (Object.keys(prevCanRef.current).length !== onChange[0]["instances"].length){
        setInstanceBtn(onChange[0])
      }
    }


    const id = setInterval(() => {
      callApi().then((value => {
        setCanData(value.props.components);
      }))
    }, 5000);
    return () => clearInterval(id);
  }, [canData])


  function writeData(event){
    setflagInstance(true)
    let name = event.target.id
    setMsg_name(name)

    let data = getComponentData(name)
    
  
    setInstanceBtn(data[0])
    
  }

  return(
    <div className={styles.container}>
      <div className={styles.devices}>
        {canData.length > 0 ? canData.map(can =>(
          <div className={styles.device} key ={can.name}>
              <button id= {can.name} onClick={e => writeData(e)} className={styles.name}> {can.name} <span className={styles.espan}>{can.instances}</span></button>
          </div>
        )): <div>Wait for data. This might take a few seconds</div>}
      </div>
      <div className={styles.information}>
        {flag ? <h3>{instanceBtn["name"]}</h3>:null}
        {flag ? instanceBtn["instances"].map(inst =>(
          <div key ={inst}>
              <button id= {inst} onClick={e => (setInstanceFilter(e.target.id), setflagInstance(false))} className={styles.name}> {inst}</button>
          </div>
        )): null}
      </div>
      <div className={styles.messages}>
          {flag && flagInstance ? Object.keys(componentData).map(instance =>(
            <div key ={instance}>
                <h4>{instance}</h4>
                {Object.keys(componentData[instance]).map(value =>( typeof componentData[instance][value] !== "object" ?
                <div key={value} className={prevCanRef.current[instance] ? (prevCanRef.current[instance][value] != componentData[instance][value] ? styles.changed: styles.notchanged): styles.notchanged}>{value}: {componentData[instance][value]}</div>  : <div key={value} className={prevCanRef.current[instance] ? (prevCanRef.current[instance][value]["_name"] != componentData[instance][value]["_name"] ? styles.changed :styles.notchanged): styles.notchanged}>{value}: {componentData[instance][value]["_name"]}</div>
                ))}
            </div>
          )): !flagInstance ? Object.keys(componentData[instanceFilter]).map(value =>( typeof componentData[instanceFilter][value] !== "object" ?
          <div key={value} className={prevCanRef.current[instanceFilter] ? (prevCanRef.current[instanceFilter][value] != componentData[instanceFilter][value] ? styles.changed: styles.notchanged): styles.notchanged}>{value}: {componentData[instanceFilter][value]}</div>: <div key={value} className={prevCanRef.current[instanceFilter] ? (prevCanRef.current[instanceFilter][value]["_name"] != componentData[instanceFilter][value]["_name"] ? styles.changed : styles.notchanged): styles.notchanged}>{value}: {componentData[instanceFilter][value]["_name"]}</div>
        )) :null}
      </div>
    </div>
  );
}
// 
export default Ninjas;